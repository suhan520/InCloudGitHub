"""
GitHub仓库扫描模块
"""
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from github import Github, GithubException
from config import GITHUB_TOKEN, AI_SEARCH_KEYWORDS, MAX_REPOS_PER_SEARCH, SEARCH_DELAY_SECONDS, MIN_DAYS_SINCE_UPDATE


class GitHubScanner:
    """GitHub仓库扫描器"""
    
    def __init__(self, token: str = GITHUB_TOKEN):
        """
        初始化GitHub扫描器
        
        Args:
            token: GitHub Personal Access Token
        """
        if not token:
            raise ValueError("GitHub Token is required. Please set GITHUB_TOKEN in .env file")
        
        # 配置超时和重试参数，避免长时间等待
        self.github = Github(
            token,
            timeout=30,  # 设置30秒超时
            retry=None   # 禁用自动重试，我们自己处理
        )
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        
    def get_rate_limit_info(self) -> Dict:
        """获取API速率限制信息"""
        rate_limit = self.github.get_rate_limit()

        # 兼容不同版本的 PyGithub 返回对象
        core = None
        if hasattr(rate_limit, 'core'):
            core = rate_limit.core
        elif hasattr(rate_limit, 'resources'):
            resources = getattr(rate_limit, 'resources')
            if isinstance(resources, dict):
                core = resources.get('core')
            elif hasattr(resources, 'core'):
                core = resources.core
        elif hasattr(rate_limit, 'rate'):
            core = rate_limit.rate
        elif hasattr(rate_limit, 'raw_data'):
            raw_data = getattr(rate_limit, 'raw_data')
            if isinstance(raw_data, dict):
                resources = raw_data.get('resources', {})
                core = resources.get('core') if isinstance(resources, dict) else None

        if core is None:
            raise RuntimeError(
                f"无法读取 GitHub API 速率限制，返回对象类型: {type(rate_limit)}"
            )

        remaining = getattr(core, 'remaining', None)
        limit = getattr(core, 'limit', None)
        reset = getattr(core, 'reset', None)

        if isinstance(core, dict):
            remaining = remaining if remaining is not None else core.get('remaining')
            limit = limit if limit is not None else core.get('limit')
            reset = reset if reset is not None else core.get('reset')

        if isinstance(reset, (int, float)):
            reset = datetime.fromtimestamp(reset)

        return {
            'remaining': remaining,
            'limit': limit,
            'reset': reset
        }
    
    def wait_for_rate_limit(self):
        """等待速率限制重置"""
        info = self.get_rate_limit_info()
        if info['remaining'] is not None and info['remaining'] < 10:
            # info['reset'] 是 datetime 对象，需要和 datetime.now() 比较
            wait_time = (info['reset'] - datetime.now()).total_seconds() + 10
            print(f"⚠️  API速率限制即将耗尽，等待 {wait_time:.0f} 秒...")
            time.sleep(max(0, wait_time))
    
    def get_user_repos(self, username: str) -> List[Dict]:
        """
        获取指定用户的所有公开仓库
        
        Args:
            username: GitHub用户名
            
        Returns:
            仓库信息列表
        """
        try:
            user = self.github.get_user(username)
            repos = []
            
            for repo in user.get_repos():
                if not repo.private:
                    repos.append({
                        'name': repo.name,
                        'full_name': repo.full_name,
                        'url': repo.html_url,
                        'clone_url': repo.clone_url,
                        'description': repo.description,
                        'updated_at': repo.updated_at,
                    })
            
            return repos
        except GithubException as e:
            print(f"❌ 获取用户仓库失败: {e}")
            return []
    
    def get_org_repos(self, org_name: str) -> List[Dict]:
        """
        获取指定组织的所有公开仓库
        
        Args:
            org_name: GitHub组织名
            
        Returns:
            仓库信息列表
        """
        try:
            org = self.github.get_organization(org_name)
            repos = []
            
            for repo in org.get_repos():
                if not repo.private:
                    repos.append({
                        'name': repo.name,
                        'full_name': repo.full_name,
                        'url': repo.html_url,
                        'clone_url': repo.clone_url,
                        'description': repo.description,
                        'updated_at': repo.updated_at,
                    })
            
            return repos
        except GithubException as e:
            print(f"❌ 获取组织仓库失败: {e}")
            return []
    
    def search_ai_repos(self, max_repos: int = MAX_REPOS_PER_SEARCH, skip_filter=None) -> List[Dict]:
        """
        搜索AI相关的GitHub项目
        
        Args:
            max_repos: 最大返回仓库数量
            skip_filter: 可选的过滤函数，接受仓库全名，返回True表示跳过该仓库
            
        Returns:
            仓库信息列表
        """
        all_repos = []
        seen_repos = set()
        skipped_count = 0
        
        for keyword in AI_SEARCH_KEYWORDS:
            try:
                print(f"🔍 搜索关键词: {keyword}")
                self.wait_for_rate_limit()
                
                # 搜索代码
                query = f'{keyword} in:file language:python'
                results = self.github.search_code(query, order='desc')
                
                # 从代码搜索结果中提取仓库
                for code in results:
                    # 如果已经找到足够的仓库，停止搜索
                    if len(all_repos) >= max_repos:
                        break
                    
                    repo = code.repository
                    
                    # 跳过私有仓库和已经见过的仓库
                    if repo.private or repo.full_name in seen_repos:
                        continue
                    
                    seen_repos.add(repo.full_name)
                    
                    # 如果提供了过滤函数，检查是否应该跳过
                    if skip_filter and skip_filter(repo.full_name):
                        skipped_count += 1
                        print(f"  ⏭️  跳过已扫描: {repo.full_name}")
                        continue  # 不计数，继续找下一个
                    
                    # 检查仓库最后更新时间是否在指定时间范围内
                    if repo.updated_at:
                        days_since_update = (datetime.now(repo.updated_at.tzinfo) - repo.updated_at).days
                        if days_since_update > MIN_DAYS_SINCE_UPDATE:
                            skipped_count += 1
                            print(f"  ⏭️  跳过长期不维护: {repo.full_name} (最后更新: {days_since_update} 天前)")
                            continue
                    
                    # 添加到结果列表
                    all_repos.append({
                        'name': repo.name,
                        'full_name': repo.full_name,
                        'url': repo.html_url,
                        'clone_url': repo.clone_url,
                        'description': repo.description,
                        'updated_at': repo.updated_at,
                    })
                
                # 延迟以避免触发速率限制
                time.sleep(SEARCH_DELAY_SECONDS)
                
                if len(all_repos) >= max_repos:
                    print(f"✅ 已找到 {len(all_repos)} 个未扫描的仓库（跳过了 {skipped_count} 个已扫描的）")
                    break
                    
            except GithubException as e:
                print(f"⚠️  搜索 '{keyword}' 时出错: {e}")
                continue
        
        if skipped_count > 0 and len(all_repos) < max_repos:
            print(f"ℹ️  找到 {len(all_repos)} 个未扫描的仓库（跳过了 {skipped_count} 个已扫描的）")
        
        return all_repos
    
    def get_repo_files(self, repo_full_name: str, path: str = "") -> List[Dict]:
        """
        获取仓库中的文件列表
        
        Args:
            repo_full_name: 仓库全名 (owner/repo)
            path: 文件路径
            
        Returns:
            文件信息列表
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            if path:
                print(f"  📁 获取目录: {path}")
            else:
                print("  📁 获取根目录")
            contents = repo.get_contents(path)
            
            files = []
            for content in contents:
                if content.type == "dir":
                    # 递归获取子目录文件
                    files.extend(self.get_repo_files(repo_full_name, content.path))
                else:
                    files.append({
                        'path': content.path,
                        'name': content.name,
                        'download_url': content.download_url,
                        'sha': content.sha,
                    })
            
            return files
        except GithubException as e:
            # 403 错误直接跳过，不等待
            if e.status == 403:
                print(f"  ⏭️  跳过: 无权访问 (403 Forbidden)")
            else:
                print(f"⚠️  获取文件列表失败: {e}")
            return []
    
    def get_file_content(self, repo_full_name: str, file_path: str) -> Optional[str]:
        """
        获取文件内容
        
        Args:
            repo_full_name: 仓库全名 (owner/repo)
            file_path: 文件路径
            
        Returns:
            文件内容（文本）
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            content = repo.get_contents(file_path)
            
            # 解码内容
            try:
                return content.decoded_content.decode('utf-8')
            except UnicodeDecodeError:
                # 如果是二进制文件，返回None
                return None
        except GithubException as e:
            # 403 错误直接跳过，不打印错误
            if e.status == 403:
                pass  # 静默跳过
            return None
