"""
事实检查器 (Fact Checker)

检测和验证生成内容中的事实性错误，特别是：
- 数值数据（股价、财务数据、统计数据）
- 日期时间
- 人名、地名、机构名
- 引用来源

架构:
┌─────────────────────────────────────────────────────────┐
│              FactChecker                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │  数值检测器                                        │  │
│  │  - 识别数值型陈述（价格、百分比、统计）            │  │
│  │  - 标记需要验证的数据点                            │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  来源验证器                                        │  │
│  │  - 检查是否有数据来源说明                          │  │
│  │  - 验证来源可靠性                                  │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  一致性检查器                                      │  │
│  │  - 检测内部矛盾                                    │  │
│  │  - 检测逻辑不一致                                  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class FactType(Enum):
    """事实类型"""
    NUMERIC = "numeric"       # 数值数据
    DATE = "date"            # 日期时间
    ENTITY = "entity"        # 实体名称
    QUOTE = "quote"          # 引用来源
    CLAIM = "claim"          # 断言/陈述


class VerificationStatus(Enum):
    """验证状态"""
    VERIFIED = "verified"       # 已验证
    UNVERIFIED = "unverified"   # 未验证
    SUSPICIOUS = "suspicious"   # 可疑
    CONTRADICTORY = "contradictory"  # 矛盾


@dataclass
class FactClaim:
    """事实断言"""
    claim_id: str
    fact_type: FactType
    content: str
    confidence: float
    source: Optional[str] = None
    status: VerificationStatus = VerificationStatus.UNVERIFIED
    context: str = ""

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "fact_type": self.fact_type.value,
            "content": self.content,
            "confidence": round(self.confidence, 2),
            "source": self.source,
            "status": self.status.value,
            "context": self.context[:100] if self.context else ""
        }


@dataclass
class FactCheckReport:
    """事实检查报告"""
    total_claims: int
    verified: int
    unverified: int
    suspicious: int
    contradictory: int
    claims: List[FactClaim]
    overall_confidence: float
    has_source_attribution: bool
    recommendations: List[str] = field(default_factory=list)

    @property
    def verification_rate(self) -> float:
        """验证通过率"""
        if self.total_claims == 0:
            return 1.0
        return self.verified / self.total_claims

    def to_dict(self) -> dict:
        return {
            "total_claims": self.total_claims,
            "verified": self.verified,
            "unverified": self.unverified,
            "suspicious": self.suspicious,
            "contradictory": self.contradictory,
            "verification_rate": round(self.verification_rate, 2),
            "overall_confidence": round(self.overall_confidence, 2),
            "has_source_attribution": self.has_source_attribution,
            "recommendations": self.recommendations
        }

    def to_summary(self) -> str:
        """生成摘要"""
        status = "通过" if self.verification_rate >= 0.8 else "需验证"
        return (
            f"事实检查{status}: {self.verified}/{self.total_claims} 已验证 "
            f"({self.verification_rate:.1%}), "
            f"{self.suspicious} 个可疑项，"
            f"{self.unverified} 个未验证项"
        )


class FactChecker:
    """事实检查器"""

    def __init__(self, llm_client: Optional[Any] = None):
        """
        初始化事实检查器

        Args:
            llm_client: 可选的 LLM 客户端，用于深度验证
        """
        self.llm_client = llm_client
        self._claim_counter = 0

    def check(self, content: str, context: Optional[Dict] = None) -> FactCheckReport:
        """
        执行事实检查

        Args:
            content: 待检查的内容
            context: 上下文信息（如查询类型、期望的数据源等）

        Returns:
            FactCheckReport: 事实检查报告
        """
        # 1. 提取事实断言
        claims = self._extract_claims(content)

        # 2. 检查数据来源
        has_source = self._check_source_attribution(content)

        # 3. 评估每个断言的可信度
        for claim in claims:
            claim.confidence = self._evaluate_claim_confidence(claim, context)

        # 4. 检测内部矛盾
        contradictions = self._detect_contradictions(claims)
        for claim_id in contradictions:
            for claim in claims:
                if claim.claim_id == claim_id:
                    claim.status = VerificationStatus.CONTRADICTORY

        # 5. 标记可疑断言
        for claim in claims:
            if claim.status != VerificationStatus.CONTRADICTORY:
                claim.status = self._evaluate_claim_status(claim, context)

        # 6. 生成报告
        return self._generate_report(claims, has_source)

    def _generate_id(self) -> str:
        """生成唯一 ID"""
        self._claim_counter += 1
        return f"claim_{self._claim_counter:03d}"

    def _extract_claims(self, content: str) -> List[FactClaim]:
        """从内容中提取事实断言"""
        claims = []

        # 1. 提取数值型断言
        numeric_claims = self._extract_numeric_claims(content)
        claims.extend(numeric_claims)

        # 2. 提取日期型断言
        date_claims = self._extract_date_claims(content)
        claims.extend(date_claims)

        # 3. 提取实体断言
        entity_claims = self._extract_entity_claims(content)
        claims.extend(entity_claims)

        # 4. 提取引用断言
        quote_claims = self._extract_quote_claims(content)
        claims.extend(quote_claims)

        return claims

    def _extract_numeric_claims(self, content: str) -> List[FactClaim]:
        """提取数值型断言"""
        claims = []

        # 匹配模式：数字 + 单位/上下文
        patterns = [
            # 股价模式：XXX 点/元，上涨/下跌 X%
            r'(\d+\.?\d*)\s*(点 | 元 | 美元 | 亿元 | %|百分之 [零一二三四五六七八九十百千万]+)',
            # 财务数据：营收 XXX 亿元
            r'(营收 | 利润 | 收入 | 成交 | 成交量)\s*(?:为 | 达 | 约)?\s*(\d+\.?\d*)\s*(亿 | 万 | 千)?\s*(元 | 美元 | 股)?',
            # 百分比：上涨/下跌 X.XX%
            r'(上涨 | 下跌 | 增长 | 下降 | 涨幅 | 跌幅)\s*(\d+\.?\d*)\s*%?',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # 获取上下文（前后 50 字符）
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end].strip()

                claim = FactClaim(
                    claim_id=self._generate_id(),
                    fact_type=FactType.NUMERIC,
                    content=match.group(0),
                    confidence=0.5,  # 初始置信度
                    context=context
                )
                claims.append(claim)

        return claims

    def _extract_date_claims(self, content: str) -> List[FactClaim]:
        """提取日期型断言"""
        claims = []

        patterns = [
            # 具体日期
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{4}-\d{2}-\d{2})',
            # 时间
            r'(\d{1,2}:\d{2})',
            # 相对时间
            r'(今日 | 昨日 | 今天 | 昨天 | 本周 | 上周 | 本月 | 上月)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                start = max(0, match.start() - 30)
                end = min(len(content), match.end() + 30)
                context = content[start:end].strip()

                claim = FactClaim(
                    claim_id=self._generate_id(),
                    fact_type=FactType.DATE,
                    content=match.group(0),
                    confidence=0.7,
                    context=context
                )
                claims.append(claim)

        return claims

    def _extract_entity_claims(self, content: str) -> List[FactClaim]:
        """提取实体断言（人名、公司名、产品名等）"""
        claims = []

        # 简化的实体检测（实际应该用 NER 模型）
        patterns = [
            # 公司名
            r'([A 股 A 股科创板创业板港股美股]+)',
            # 指数名
            r'(上证综指 | 深证成指 | 创业板指 | 科创 50 | 恒生指数 | 纳斯达克)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                claim = FactClaim(
                    claim_id=self._generate_id(),
                    fact_type=FactType.ENTITY,
                    content=match.group(0),
                    confidence=0.8,
                    context=match.group(0)
                )
                claims.append(claim)

        return claims

    def _extract_quote_claims(self, content: str) -> List[FactClaim]:
        """提取引用断言"""
        claims = []

        patterns = [
            # 数据来源
            r'数据来源 [:：]?\s*(.+?)(?:\n|$)',
            # 根据/据
            r'(?:根据 | 据 | 引用 自)\s*([^\n,，.。]{5,50})',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                claim = FactClaim(
                    claim_id=self._generate_id(),
                    fact_type=FactType.QUOTE,
                    content=match.group(0),
                    confidence=0.6,
                    source=match.group(1) if len(match.groups()) > 0 else None
                )
                claims.append(claim)

        return claims

    def _check_source_attribution(self, content: str) -> bool:
        """检查是否有数据来源说明"""
        source_keywords = [
            "数据来源", "数据来源：", "数据来源:",
            "根据", "据悉", "据报道",
            "数据显示", "统计显示",
            "来自", "引用",
        ]

        for keyword in source_keywords:
            if keyword in content:
                return True

        return False

    def _evaluate_claim_confidence(
        self,
        claim: FactClaim,
        context: Optional[Dict] = None
    ) -> float:
        """评估断言的置信度"""
        base_confidence = 0.5

        # 有数据来源加分
        if claim.source:
            base_confidence += 0.2

        # 数值型断言需要来源
        if claim.fact_type == FactType.NUMERIC:
            if not claim.source:
                base_confidence = 0.3  # 无数值来源，置信度低

        # 日期型断言如果有上下文支持，置信度较高
        if claim.fact_type == FactType.DATE:
            base_confidence = max(base_confidence, 0.6)

        # 实体型断言通常是事实，置信度高
        if claim.fact_type == FactType.ENTITY:
            base_confidence = max(base_confidence, 0.8)

        # 有上下文支持加分
        if claim.context and len(claim.context) > 20:
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    def _detect_contradictions(self, claims: List[FactClaim]) -> List[str]:
        """检测内部矛盾"""
        contradictory_ids = []

        # 检查数值矛盾（如同一指标不同数值）
        numeric_claims = [c for c in claims if c.fact_type == FactType.NUMERIC]

        # 简单的矛盾检测：同一上下文中相反的陈述
        # 这里可以做更复杂的 NLP 分析

        return contradictory_ids

    def _evaluate_claim_status(
        self,
        claim: FactClaim,
        context: Optional[Dict] = None
    ) -> VerificationStatus:
        """评估断言的验证状态"""
        # 低置信度的数值断言标记为可疑
        if claim.fact_type == FactType.NUMERIC and claim.confidence < 0.4:
            return VerificationStatus.SUSPICIOUS

        # 中等置信度为未验证
        if claim.confidence < 0.6:
            return VerificationStatus.UNVERIFIED

        # 高置信度为已验证（假设有来源支持）
        if claim.confidence >= 0.8 and claim.source:
            return VerificationStatus.VERIFIED

        return VerificationStatus.UNVERIFIED

    def _generate_report(
        self,
        claims: List[FactClaim],
        has_source: bool
    ) -> FactCheckReport:
        """生成事实检查报告"""
        verified = sum(1 for c in claims if c.status == VerificationStatus.VERIFIED)
        unverified = sum(1 for c in claims if c.status == VerificationStatus.UNVERIFIED)
        suspicious = sum(1 for c in claims if c.status == VerificationStatus.SUSPICIOUS)
        contradictory = sum(1 for c in claims if c.status == VerificationStatus.CONTRADICTORY)

        # 计算整体置信度
        if claims:
            overall_confidence = sum(c.confidence for c in claims) / len(claims)
        else:
            overall_confidence = 1.0

        # 生成建议
        recommendations = []

        if not has_source and claims:
            recommendations.append("建议添加数据来源说明，增强可信度")

        if suspicious > 0:
            recommendations.append(f"发现{suspicious}个可疑数据点，建议核实")

        if unverified > 0:
            recommendations.append(f"有{unverified}个未验证断言，建议补充来源")

        if not recommendations and claims:
            recommendations.append("数据可信度较高，建议保留来源说明")

        return FactCheckReport(
            total_claims=len(claims),
            verified=verified,
            unverified=unverified,
            suspicious=suspicious,
            contradictory=contradictory,
            claims=claims,
            overall_confidence=overall_confidence,
            has_source_attribution=has_source,
            recommendations=recommendations
        )


def create_fact_checker(llm_client: Optional[Any] = None) -> FactChecker:
    """工厂函数：创建事实检查器"""
    return FactChecker(llm_client=llm_client)
