#!/usr/bin/env python3
"""
领域标签测试脚本

验证所有 Agent 的领域标签分类和统计
"""

import sys
from pathlib import Path
from collections import defaultdict

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml

from termcolor import cprint
from termcolor import cprint


def cprint(text, color=None, attrs=None):
    """简化版 cprint"""
    print(text)


def load_all_agents():
    """加载所有 Agent 配置"""
    # Try simple_agent first, then customization
    builtin_agents_dir = Path(__file__).parent.parent / "simple_agent" / "builtin_agents" / "configs"
    if not builtin_agents_dir.exists():
        builtin_agents_dir = Path(__file__).parent.parent / "builtin_agents" / "configs"

    agents = []

    for yaml_file in builtin_agents_dir.glob("*.yaml"):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            config['_file'] = yaml_file.stem
            agents.append(config)

    return agents


def test_domain_coverage(agents):
    """测试领域覆盖"""
    domains_count = defaultdict(int)
    agents_by_domain = defaultdict(list)
    
    for agent in agents:
        name = agent.get('name', agent['_file'])
        domains = agent.get('domains', [])
        
        if not domains:
            cprint(f"⚠ {name} 缺少领域标签", "yellow")
        
        for domain in domains:
            domains_count[domain] += 1
            agents_by_domain[domain].append(name)
    
    return domains_count, agents_by_domain


def test_multi_domain_agents(agents):
    """测试跨领域 Agent"""
    multi_domain = []
    
    for agent in agents:
        name = agent.get('name', agent['_file'])
        domains = agent.get('domains', [])
        
        if len(domains) > 1:
            multi_domain.append((name, domains))
    
    return multi_domain


def print_domain_statistics(domains_count, agents_by_domain):
    """打印领域统计"""
    cprint("\n" + "=" * 70, "cyan", attrs=["bold"])
    cprint("领域分布统计", "cyan", attrs=["bold"])
    cprint("=" * 70, "cyan", attrs=["bold"])
    print()
    
    # 按领域分组
    domain_groups = {
        "通用": ["general", "project_management"],
        "软件工程": ["software_engineering", "programming", "quality_assurance", 
                     "system_design", "technical_writing", "devops"],
        "人工智能": ["artificial_intelligence", "machine_learning", 
                     "natural_language_processing", "computer_vision", 
                     "research", "large_language_models"],
        "数据科学": ["data_science", "analytics"],
        "金融": ["finance", "investment", "quantitative_trading", 
                "risk_management", "wealth_management", 
                "regulatory_compliance", "credit_risk", "trading"],
    }
    
    domain_names = {
        "general": "通用",
        "software_engineering": "软件工程",
        "programming": "编程",
        "quality_assurance": "质量保证",
        "system_design": "系统设计",
        "technical_writing": "技术写作",
        "devops": "DevOps",
        "project_management": "项目管理",
        "data_science": "数据科学",
        "analytics": "分析",
        "artificial_intelligence": "人工智能",
        "machine_learning": "机器学习",
        "natural_language_processing": "自然语言处理",
        "computer_vision": "计算机视觉",
        "research": "研究",
        "large_language_models": "大语言模型",
        "finance": "金融",
        "investment": "投资",
        "quantitative_trading": "量化交易",
        "risk_management": "风险管理",
        "wealth_management": "财富管理",
        "regulatory_compliance": "合规监管",
        "credit_risk": "信用风险",
        "trading": "交易",
    }
    
    for group_name, domains in domain_groups.items():
        print(f"\n## {group_name}")
        print("-" * 60)
        
        for domain in domains:
            if domain in domains_count:
                count = domains_count[domain]
                domain_cn = domain_names.get(domain, domain)
                agents = agents_by_domain[domain]
                print(f"  {domain_cn:12} ({count:2}个): {', '.join(agents)}")
    
    print()
    cprint("=" * 70, "cyan", attrs=["bold"])

    # 总体统计
    total_domain_refs = sum(domains_count.values())

    print(f"\n总体统计:")
    print(f"  - Agent 总数：{len(agents_by_domain)}")
    print(f"  - 领域标签引用：{total_domain_refs} 次")
    print(f"  - 领域类别数：{len(domains_count)} 个")
    print(f"  - 平均每个 Agent 领域数：{total_domain_refs / max(len(agents_by_domain), 1):.2f}")


def print_multi_domain_agents(multi_domain):
    """打印跨领域 Agent"""
    cprint("\n" + "=" * 70, "cyan", attrs=["bold"])
    cprint("跨领域 Agent", "cyan", attrs=["bold"])
    cprint("=" * 70, "cyan", attrs=["bold"])
    print()
    
    if not multi_domain:
        cprint("未找到跨领域 Agent", "yellow")
        return
    
    for name, domains in sorted(multi_domain, key=lambda x: len(x[1]), reverse=True):
        domains_str = " + ".join(domains)
        print(f"  • {name:20} [{domains_str}]")
    
    print()
    cprint(f"共 {len(multi_domain)} 个跨领域 Agent", "green")


def main():
    """主函数"""
    cprint("\n" + "=" * 70, "cyan", attrs=["bold"])
    cprint("Agent 领域标签测试", "cyan", attrs=["bold"])
    cprint("=" * 70, "cyan", attrs=["bold"])
    print()
    
    # 加载所有 Agent
    agents = load_all_agents()
    cprint(f"✓ 加载 {len(agents)} 个 Agent 配置", "green")
    
    # 测试领域覆盖
    domains_count, agents_by_domain = test_domain_coverage(agents)
    
    # 测试跨领域 Agent
    multi_domain = test_multi_domain_agents(agents)
    
    # 打印统计
    print_domain_statistics(domains_count, agents_by_domain)
    print_multi_domain_agents(multi_domain)
    
    # 验证结果
    print()
    cprint("=" * 70, "cyan", attrs=["bold"])
    
    issues = []
    
    # 检查是否有 Agent 缺少领域标签
    for agent in agents:
        if not agent.get('domains'):
            issues.append(f"{agent.get('name')} 缺少领域标签")
    
    # 检查领域标签是否合理
    valid_domains = {
        "general", "software_engineering", "programming", "quality_assurance",
        "system_design", "technical_writing", "devops", "project_management",
        "data_science", "analytics", "artificial_intelligence", "machine_learning",
        "natural_language_processing", "computer_vision", "research",
        "large_language_models", "finance", "investment", "quantitative_trading",
        "risk_management", "wealth_management", "regulatory_compliance",
        "credit_risk", "trading"
    }
    
    for agent in agents:
        for domain in agent.get('domains', []):
            if domain not in valid_domains:
                issues.append(f"{agent.get('name')} 使用了未知领域标签：{domain}")
    
    if issues:
        cprint(f"✗ 发现 {len(issues)} 个问题:", "red")
        for issue in issues[:5]:
            print(f"  - {issue}")
    else:
        cprint("✓ 领域标签配置正确", "green")
    
    cprint("=" * 70, "cyan", attrs=["bold"])
    print()


if __name__ == "__main__":
    main()
