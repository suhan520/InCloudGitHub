"""
主扫描器模块 - 整合所有功能
"""
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from github_scanner import GitHubScanner
from secret_detector import SecretDetector
from report_generator import ReportGenerator
from scan_history import ScanHistory
from config import MIN_DAYS_SINCE_UPDATE


class CloudScanner:
    """云上扫描器 - 主要扫描逻辑"""
    
    def __init__(self, github_token: str, skip_scanned: bool = True, timeout_minutes: int = 50, output_dir: str = None):
        """
        初始化扫描器
        
        Args:
            github_token: GitHub Personal Access Token
            skip_scanned: 是否跳过已扫描的仓库 (默认: True)
            timeout_minutes: 扫描超时时间（分钟），默认50分钟
            output_dir: 报告输出目录
        """
        self.github_scanner = GitHubScanner(github_token)
        self.secret_detector = SecretDetector()
        self.report_generator = ReportGenerator(output_dir=output_dir)
        self.scan_history = ScanHistory()
        self.skip_scanned = skip_scanned
        self.timeout_seconds = timeout_minutes * 60
        self.scan_start_time = None
    
    def _is_timeout(self) -> bool:
        """检查是否超时"""
        if self.scan_start_time is None:
            return False
        elapsed = time.time() - self.scan_start_time
        return elapsed >= self.timeout_seconds
    
    def _check_timeout(self, current_idx: int, total_repos: int) -> bool:
        """
        检查是否超时，如果超时则打印信息并返回True
        
        Args:
            current_idx: 当前扫描的仓库索引
            total_repos: 总仓库数
            
        Returns:
            是否超时
        """
        if self._is_timeout():
            elapsed_minutes = (time.time() - self.scan_start_time) / 60
            print(f"\n⏰ 扫描超时（已运行 {elapsed_minutes:.1f} 分钟）")
            print(f"✅ 已完成 {current_idx}/{total_repos} 个仓库的扫描")
            print(f"💾 已保存前面的扫描数据，剩余 {total_repos - current_idx} 个仓库将在下次扫描时处理")
            return True
        return False
    
    def scan_user(self, username: str) -> str:
        """
        扫描指定用户的所有公开仓库
        
        Args:
            username: GitHub用户名
            
        Returns:
            报告文件路径
        """
        print(f"🚀 开始扫描用户: {username}")
        scan_start_time = datetime.now()
        self.scan_start_time = time.time()  # 开始计时
        
        # 获取用户的所有仓库
        repos = self.github_scanner.get_user_repos(username)
        print(f"📦 找到 {len(repos)} 个公开仓库")
        
        # 过滤长时间不维护的仓库
        repos, old_count = self._filter_old_repos(repos)
        if old_count > 0:
            print(f"⏭️  跳过 {old_count} 个长期不维护的仓库 (最后更新超过 {MIN_DAYS_SINCE_UPDATE} 天)")
            print(f"📦 剩余 {len(repos)} 个活跃仓库待检查")
        
        # 过滤已扫描的仓库
        repos_to_scan, skipped_count = self._filter_scanned_repos(repos)
        if skipped_count > 0:
            print(f"⏭️  跳过 {skipped_count} 个已扫描的仓库")
            print(f"📦 需要扫描 {len(repos_to_scan)} 个新仓库")
        
        # 扫描所有仓库
        all_findings = []
        for idx, repo in enumerate(repos_to_scan, 1):
            # 检查超时
            if self._check_timeout(idx - 1, len(repos_to_scan)):
                break
            
            print(f"🔍 [{idx}/{len(repos_to_scan)}] 扫描仓库: {repo['full_name']}")
            findings = self._scan_repository(repo, scan_type=f"user:{username}")
            all_findings.extend(findings)
        
        # 生成报告
        print(f"\n📝 生成报告...")
        report_path = self.report_generator.generate_report(
            all_findings, 
            scan_start_time,
            scan_type=f"user:{username}"
        )
        
        # 打印摘要
        summary = self.report_generator.generate_summary(report_path, len(all_findings))
        print(summary)
        
        return report_path
    
    def scan_organization(self, org_name: str) -> str:
        """
        扫描指定组织的所有公开仓库
        
        Args:
            org_name: GitHub组织名
            
        Returns:
            报告文件路径
        """
        print(f"🚀 开始扫描组织: {org_name}")
        scan_start_time = datetime.now()
        self.scan_start_time = time.time()  # 开始计时
        
        # 获取组织的所有仓库
        repos = self.github_scanner.get_org_repos(org_name)
        print(f"📦 找到 {len(repos)} 个公开仓库")
        
        # 过滤长时间不维护的仓库
        repos, old_count = self._filter_old_repos(repos)
        if old_count > 0:
            print(f"⏭️  跳过 {old_count} 个长期不维护的仓库 (最后更新超过 {MIN_DAYS_SINCE_UPDATE} 天)")
            print(f"📦 剩余 {len(repos)} 个活跃仓库待检查")
        
        # 过滤已扫描的仓库
        repos_to_scan, skipped_count = self._filter_scanned_repos(repos)
        if skipped_count > 0:
            print(f"⏭️  跳过 {skipped_count} 个已扫描的仓库")
            print(f"📦 需要扫描 {len(repos_to_scan)} 个新仓库")
        
        # 扫描所有仓库
        all_findings = []
        for idx, repo in enumerate(repos_to_scan, 1):
            # 检查超时
            if self._check_timeout(idx - 1, len(repos_to_scan)):
                break
            
            print(f"🔍 [{idx}/{len(repos_to_scan)}] 扫描仓库: {repo['full_name']}")
            findings = self._scan_repository(repo, scan_type=f"org:{org_name}")
            all_findings.extend(findings)
        
        # 生成报告
        print(f"\n📝 生成报告...")
        report_path = self.report_generator.generate_report(
            all_findings,
            scan_start_time,
            scan_type=f"org:{org_name}"
        )
        
        # 打印摘要
        summary = self.report_generator.generate_summary(report_path, len(all_findings))
        print(summary)
        
        return report_path
    
    def scan_ai_projects(self, max_repos: int = 50) -> str:
        """
        自动搜索并扫描AI相关项目
        
        Args:
            max_repos: 最大扫描仓库数
            
        Returns:
            报告文件路径
        """
        print(f"🚀 开始自动搜索 AI 相关项目")
        print(f"🎯 目标: 找到并扫描 {max_repos} 个未扫描的仓库")
        scan_start_time = datetime.now()
        self.scan_start_time = time.time()  # 开始计时
        
        # 定义过滤函数：检查仓库是否已扫描
        def is_scanned(repo_full_name: str) -> bool:
            return self.scan_history.is_scanned(repo_full_name)
        
        # 搜索仓库，实时过滤已扫描的
        # 搜索过程会自动跳过已扫描的仓库，直到找到足够数量的新仓库
        repos_to_scan = self.github_scanner.search_ai_repos(
            max_repos=max_repos,
            skip_filter=is_scanned if self.skip_scanned else None
        )
        
        print(f"📦 找到 {len(repos_to_scan)} 个待扫描的仓库")
        
        # 扫描所有仓库
        all_findings = []
        for idx, repo in enumerate(repos_to_scan, 1):
            # 检查超时
            if self._check_timeout(idx - 1, len(repos_to_scan)):
                break
            
            print(f"🔍 [{idx}/{len(repos_to_scan)}] 扫描仓库: {repo['full_name']}")
            findings = self._scan_repository(repo, scan_type="auto:ai-projects")
            all_findings.extend(findings)
        
        # 生成报告
        print(f"\n📝 生成报告...")
        report_path = self.report_generator.generate_report(
            all_findings,
            scan_start_time,
            scan_type="auto:ai-projects"
        )
        
        # 打印摘要
        summary = self.report_generator.generate_summary(report_path, len(all_findings))
        print(summary)
        
        return report_path
    
    def scan_single_repo(self, repo_full_name: str) -> str:
        """
        扫描单个仓库
        
        Args:
            repo_full_name: 仓库全名 (owner/repo)
            
        Returns:
            报告文件路径
        """
        print(f"🚀 开始扫描仓库: {repo_full_name}")
        scan_start_time = datetime.now()
        
        # 构建仓库信息
        repo_info = {
            'full_name': repo_full_name,
            'url': f"https://github.com/{repo_full_name}",
            'clone_url': f"https://github.com/{repo_full_name}.git",
        }
        
        # 扫描仓库
        findings = self._scan_repository(repo_info)
        
        # 生成报告
        print(f"\n📝 生成报告...")
        report_path = self.report_generator.generate_report(
            findings,
            scan_start_time,
            scan_type=f"single:{repo_full_name}"
        )
        
        # 打印摘要
        summary = self.report_generator.generate_summary(report_path, len(findings))
        print(summary)
        
        return report_path
    
    def _filter_scanned_repos(self, repos: List[Dict]) -> tuple:
        """
        过滤已扫描的仓库
        
        Args:
            repos: 仓库列表
            
        Returns:
            (需要扫描的仓库列表, 跳过的仓库数量)
        """
        if not self.skip_scanned:
            return repos, 0
        
        repos_to_scan = []
        skipped_count = 0
        
        for repo in repos:
            repo_name = repo.get('full_name', '')
            if self.scan_history.is_scanned(repo_name):
                skipped_count += 1
            else:
                repos_to_scan.append(repo)
        
        return repos_to_scan, skipped_count
    
    def _filter_old_repos(self, repos: List[Dict]) -> tuple:
        """
        过滤长时间不维护的仓库（最后更新超过MIN_DAYS_SINCE_UPDATE天的仓库）
        
        Args:
            repos: 仓库列表
            
        Returns:
            (有活跃更新的仓库列表, 跳过的仓库数量)
        """
        repos_to_scan = []
        skipped_count = 0
        
        for repo in repos:
            updated_at = repo.get('updated_at')
            repo_name = repo.get('full_name', 'unknown')
            
            if updated_at:
                # 处理 datetime 的时区信息，确保能够比较
                current_time = datetime.now(updated_at.tzinfo) if updated_at.tzinfo else datetime.now()
                days_since_update = (current_time - updated_at).days
                
                if days_since_update > MIN_DAYS_SINCE_UPDATE:
                    skipped_count += 1
                    print(f"  ⏭️  跳过长期不维护: {repo_name} (最后更新: {days_since_update} 天前)")
                else:
                    repos_to_scan.append(repo)
            else:
                # 如果没有更新时间信息，默认包含
                repos_to_scan.append(repo)
        
        return repos_to_scan, skipped_count
    
    def _scan_repository(self, repo: Dict, scan_type: str = "unknown") -> List[Dict]:
        """
        扫描单个仓库
        
        Args:
            repo: 仓库信息字典
            scan_type: 扫描类型
            
        Returns:
            发现的敏感信息列表
        """
        findings = []
        scan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        repo_name = repo.get('full_name', 'unknown')
        
        try:
            # 获取仓库文件列表
            files = self.github_scanner.get_repo_files(repo['full_name'])
            
            # 如果获取文件列表失败（例如403错误），直接返回
            if not files:
                # 记录到扫描历史，避免下次再扫
                self.scan_history.mark_as_scanned(repo_name, 0, f"{scan_type}:no-access")
                return findings
            
            # 扫描每个文件
            print(f"  📄 共找到 {len(files)} 个文件（含子目录）")
            for file_info in files:
                # 检查是否应该扫描该文件
                if not self.secret_detector.should_scan_file(file_info['path']):
                    continue
                
                # 获取文件内容
                content = self.github_scanner.get_file_content(
                    repo['full_name'],
                    file_info['path']
                )
                
                if content:
                    # 检测敏感信息
                    secrets = self.secret_detector.detect_secrets_in_text(
                        content,
                        file_info['path']
                    )
                    
                    # 添加仓库信息
                    for secret in secrets:
                        secret['repo_url'] = repo.get('url', f"https://github.com/{repo_name}")
                        secret['repo_name'] = repo['full_name']
                        secret['scan_time'] = scan_time
                        findings.append(secret)
            
            # 去重和过滤
            findings = self.secret_detector.deduplicate_findings(findings)
            findings = self.secret_detector.filter_high_confidence(findings)
            
            if findings:
                print(f"  ⚠️  发现 {len(findings)} 个潜在问题")
            else:
                print(f"  ✅ 未发现明显问题")
            
            # 记录到扫描历史
            self.scan_history.mark_as_scanned(repo_name, len(findings), scan_type)
                
        except Exception as e:
            error_msg = str(e)
            # 403错误静默处理
            if "403" in error_msg or "Forbidden" in error_msg:
                print(f"  ⏭️  跳过: 无权访问")
                self.scan_history.mark_as_scanned(repo_name, 0, f"{scan_type}:forbidden")
            else:
                print(f"  ❌ 扫描失败: {e}")
                # 即使扫描失败，也记录以避免反复尝试
                self.scan_history.mark_as_scanned(repo_name, 0, f"{scan_type}:failed")
        
        return findings
