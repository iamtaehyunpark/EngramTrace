"""
Node structure for EngramFlow.
"""

class Node:
    def __init__(self, entity_text: str, spatial_coord: tuple[float, float], time_stamp: float):
        """
        A lightweight container representing a full-sentence propositional statement.
        As per the EngramFlow architecture, Nodes do NOT hold embeddings.
        """
        self.entity: str = entity_text          
        self.spatial_id: tuple[float, float] = spatial_coord 
        self.time_stamp: float = time_stamp

    def __repr__(self):
        return f"Node(entity='{self.entity}', spatial_id='{self.spatial_id}', time_stamp='{self.time_stamp}')"
