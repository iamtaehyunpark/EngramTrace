import numpy as np
from typing import Literal

# Applying Rhetorical Structure Theory (RST) for strict directionality and logical flow
RelationType = Literal[
    "SUPPORTS", "CONTRADICTS", "ELABORATES", 
    "CAUSES", "RESULTS_FROM", "PRECEDES", "CONTRASTS_WITH", "IS_CHILD_OF_ROOT"
]

class Edge:
    def __init__(self, source: Node, relation: RelationType, target: Node, embedding_model):
        self.source: Node = source
        self.target: Node = target
        self.relation: RelationType = relation
        
        self.embedding: np.ndarray = self._generate_synaptic_embedding(embedding_model)

    def _generate_synaptic_embedding(self, embedding_model) -> np.ndarray:
        """
        Calculates E_edge = Embed(Source.text + Relation.text + Target.text)
        This shifts the semantic intelligence from the node to the logical flow.
        """
        combined_text = f"{self.source.entity} {self.relation} {self.target.entity}"
        return embedding_model.generate_synaptic_embedding(combined_text)

    def __repr__(self):
        return f"Edge({self.source.entity} --[{self.relation}]--> {self.target.entity})"
