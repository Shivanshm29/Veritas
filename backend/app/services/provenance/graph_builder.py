from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.schemas.provenance import (
    ProvenanceEdge,
    ProvenanceGraphResponse,
    ProvenanceNode,
    ProvenanceTimelineEntry,
)


def detect_cycles_in_graph(edges: List[ProvenanceEdge]) -> Tuple[bool, List[str]]:
    """
    Enforces multi-hop cycle detection across the provenance graph using DFS three-color tracking.
    Returns (cycle_detected, cycle_path_nodes).
    Ensures that derivations and provenance links form a strictly valid Directed Acyclic Graph (DAG).
    """
    adj: Dict[str, List[str]] = defaultdict(list)
    nodes: Set[str] = set()

    for edge in edges:
        adj[edge.source].append(edge.target)
        nodes.add(edge.source)
        nodes.add(edge.target)

    # 0 = unvisited, 1 = visiting (in recursion stack), 2 = visited
    visited: Dict[str, int] = {node: 0 for node in nodes}
    cycle_path: List[str] = []

    def dfs(curr: str, path: List[str]) -> bool:
        visited[curr] = 1
        path.append(curr)

        for neighbor in adj[curr]:
            if visited[neighbor] == 1:
                # Cycle found!
                cycle_start = path.index(neighbor)
                cycle_path.extend(path[cycle_start:] + [neighbor])
                return True
            if visited[neighbor] == 0:
                if dfs(neighbor, path):
                    return True

        visited[curr] = 2
        path.pop()
        return False

    for node in nodes:
        if visited[node] == 0:
            if dfs(node, []):
                return True, cycle_path

    return False, []


def build_provenance_graph(
    investigation_id: str,
    nodes: List[ProvenanceNode],
    edges: List[ProvenanceEdge],
    timeline_entries: Optional[List[ProvenanceTimelineEntry]] = None,
) -> ProvenanceGraphResponse:
    """
    Constructs the verified investigation evidence graph, validates DAG acyclicity,
    and returns a structured graph response with timeline.
    """
    has_cycle, cycle_path = detect_cycles_in_graph(edges)

    timeline = timeline_entries or []
    # If no explicit timeline is passed, synthesize from node timestamps
    if not timeline:
        for node in nodes:
            if node.timestamp:
                timeline.append(
                    ProvenanceTimelineEntry(
                        timestamp=node.timestamp.isoformat() if isinstance(node.timestamp, datetime) else str(node.timestamp),
                        event=f"Node registered: {node.type}",
                        entity_id=node.id,
                        entity_type=node.type,
                        description=f"Entity '{node.label}' added to investigation graph.",
                    )
                )
        timeline.sort(key=lambda x: x.timestamp)

    return ProvenanceGraphResponse(
        investigation_id=investigation_id,
        is_dag=not has_cycle,
        cycle_detected=has_cycle,
        nodes=nodes,
        edges=edges,
        timeline=timeline,
    )
