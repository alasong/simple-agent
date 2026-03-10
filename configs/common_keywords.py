"""
通用关键词配置
避免在代码中硬编码关键词列表
"""

import os
from typing import Dict, List


class CommonKeywordsConfig:
    """
    通用关键词配置 - 从 YAML 文件加载

    避免在代码中硬编码关键词列表
    """

    _config: Dict = None
    _loaded: bool = False

    # ========== 默认关键词 ==========

    # 复杂度判断关键词
    _default_complexity_keywords = [
        "设计", "架构", "系统", "复杂", "多个", "完整", "从 0",
        "项目", "流程", "方案", "规划"
    ]

    # 审查通过关键词（英文和中文）
    _default_approval_keywords = [
        "lgtm", "通过", "approved", "looks good", "完美", "没问题",
        "同意", "确认", "ok", "good"
    ]

    # 技能关键词映射
    _default_skill_keywords = {
        'coding': ['code', 'develop', 'program', 'write', 'implement', '编码', '开发', '实现'],
        'testing': ['test', 'qa', 'verify', 'validate', '测试', '验证'],
        'reviewing': ['review', 'audit', 'check', 'inspect', '审查', '审核', '检查'],
        'analysis': ['analyz', 'research', 'investigat', '分析', '研究', '调查'],
        'planning': ['plan', 'design', 'architect', '计划', '设计', '架构'],
        'writing': ['write', 'document', 'explain', '文档', '说明', '写作'],
        'debugging': ['debug', 'fix', 'troubleshoot', '调试', '修复', '解决'],
    }

    @classmethod
    def _load_config(cls):
        """从 YAML 加载配置"""
        if cls._loaded:
            return

        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'configs',
            'common_keywords.yaml'
        )

        try:
            import yaml
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    cls._config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"[Warning] 加载通用关键词配置失败：{e}，使用默认值")
            cls._config = {}

        cls._loaded = True

    @classmethod
    def _get_list(cls, section: str, key: str, default: List) -> List:
        """获取列表配置"""
        if not cls._loaded:
            cls._load_config()

        if cls._config and section in cls._config:
            result = cls._config[section].get(key)
            if result:
                return list(set(default + result))
        return default

    @classmethod
    def _get_dict(cls, section: str, key: str, default: Dict) -> Dict:
        """获取字典配置"""
        if not cls._loaded:
            cls._load_config()

        if cls._config and section in cls._config:
            result = cls._config[section].get(key)
            if result:
                # 合并默认值和配置值
                merged = dict(default)
                merged.update(result)
                return merged
        return default

    # ========== 复杂度判断关键词 ==========
    @classmethod
    def get_complexity_keywords(cls) -> List[str]:
        """获取复杂度判断关键词"""
        return cls._get_list('complexity', 'keywords', cls._default_complexity_keywords)

    # ========== 审查通过关键词 ==========
    @classmethod
    def get_approval_keywords(cls) -> List[str]:
        """获取审查通过关键词"""
        return cls._get_list('approval', 'keywords', cls._default_approval_keywords)

    # ========== 技能关键词映射 ==========
    @classmethod
    def get_skill_keywords(cls) -> Dict[str, List[str]]:
        """获取技能关键词映射"""
        return cls._get_dict('skills', 'keywords', cls._default_skill_keywords)

    # ========== 特定技能的关键词 ==========
    @classmethod
    def get_coding_keywords(cls) -> List[str]:
        """获取编码相关关键词"""
        skills = cls.get_skill_keywords()
        return skills.get('coding', cls._default_skill_keywords['coding'])

    @classmethod
    def get_testing_keywords(cls) -> List[str]:
        """获取测试相关关键词"""
        skills = cls.get_skill_keywords()
        return skills.get('testing', cls._default_skill_keywords['testing'])

    @classmethod
    def get_reviewing_keywords(cls) -> List[str]:
        """获取审查相关关键词"""
        skills = cls.get_skill_keywords()
        return skills.get('reviewing', cls._default_skill_keywords['reviewing'])

    @classmethod
    def get_analysis_keywords(cls) -> List[str]:
        """获取分析相关关键词"""
        skills = cls.get_skill_keywords()
        return skills.get('analysis', cls._default_skill_keywords['analysis'])

    @classmethod
    def get_planning_keywords(cls) -> List[str]:
        """获取规划相关关键词"""
        skills = cls.get_skill_keywords()
        return skills.get('planning', cls._default_skill_keywords['planning'])

    @classmethod
    def get_writing_keywords(cls) -> List[str]:
        """获取写作相关关键词"""
        skills = cls.get_skill_keywords()
        return skills.get('writing', cls._default_skill_keywords['writing'])

    @classmethod
    def get_debugging_keywords(cls) -> List[str]:
        """获取调试相关关键词"""
        skills = cls.get_skill_keywords()
        return skills.get('debugging', cls._default_skill_keywords['debugging'])
