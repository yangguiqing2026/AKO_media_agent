"""
Evolution Layer - 自我学习进化模块
三层进化架构：记忆层 → 学习层 → 涌现层
贯穿现有五层架构的进化能力
"""

from src.evolution.memory_layer.content_dna import ContentDNA
from src.evolution.memory_layer.failure_case import FailureCaseLibrary
from src.evolution.memory_layer.reader_evolution import ReaderEvolution
from src.evolution.memory_layer.cognition_graph import AKOCognitionGraph
from src.evolution.learning_layer.performance_learner import PerformanceDeepLearning
from src.evolution.learning_layer.feedback_learner import FeedbackSemanticLearning
from src.evolution.learning_layer.competitor_learner import CompetitorPatternLearning
from src.evolution.learning_layer.knowledge_graph import IndustryKnowledgeGraph
from src.evolution.emergence_layer.content_discovery import ContentFormDiscovery
from src.evolution.emergence_layer.cross_domain import CrossDomainTransfer
from src.evolution.emergence_layer.auto_tool import AutoToolDevelopment
from src.evolution.emergence_layer.co_creation import ReaderCoCreation

__all__ = [
    "ContentDNA", "FailureCaseLibrary", "ReaderEvolution", "AKOCognitionGraph",
    "PerformanceDeepLearning", "FeedbackSemanticLearning",
    "CompetitorPatternLearning", "IndustryKnowledgeGraph",
    "ContentFormDiscovery", "CrossDomainTransfer",
    "AutoToolDevelopment", "ReaderCoCreation",
]
