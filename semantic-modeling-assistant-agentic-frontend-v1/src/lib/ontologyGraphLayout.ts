import dagre from 'dagre';
import { Node, Edge } from '@xyflow/react';
import { OntologyModel, OntologyClassModel, OntologyRelationshipModel, OntologyAttributeModel } from './api';
import { ChangeType } from '@/store/ontologyChangesStore';

export interface GraphNode extends Node {
  id: string;
  type: 'classNode';
  data: {
    label: string;
    classModel: OntologyClassModel;
    attributes: OntologyAttributeModel[];
    childCount: number;
    attributeCount: number;
    relationshipCount: number;
    changeType?: ChangeType | null;
  };
  position: { x: number; y: number };
}

export interface GraphEdge extends Edge {
  id: string;
  source: string;
  target: string;
  label?: string;
  type?: 'default' | 'step' | 'smoothstep' | 'straight';
  data?: {
    relationship?: OntologyRelationshipModel;
    isInheritance?: boolean;
    changeType?: ChangeType | null;
  };
}

const NODE_WIDTH = 300;
const NODE_HEIGHT = 120;

/**
 * Transform ontology model into React Flow nodes and edges
 */
export function buildGraphData(ontology: OntologyModel | null): {
  nodes: GraphNode[];
  edges: GraphEdge[];
} {
  if (!ontology) {
    return { nodes: [], edges: [] };
  }

  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];

  // Create nodes for each class
  ontology.classes?.forEach((classModel) => {
    const childCount = ontology.classes?.filter(
      (c) => c.parent_classes?.includes(classModel.uri)
    ).length || 0;

    const classAttributes = ontology.attributes?.filter(
      (attr) => attr.domain_class === classModel.uri
    ) || [];

    const attributeCount = classAttributes.length;

    const relationshipCount = ontology.relationships?.filter(
      (rel) => rel.domain_class === classModel.uri
    ).length || 0;

    nodes.push({
      id: classModel.uri,
      type: 'classNode',
      data: {
        label: classModel.label,
        classModel,
        attributes: classAttributes,
        childCount,
        attributeCount,
        relationshipCount,
      },
      position: { x: 0, y: 0 }, // Will be set by Dagre
    });
  });

  // Create edges for inheritance relationships (parent_classes)
  // Arrow direction: from child (specialized) to parent (generic)
  ontology.classes?.forEach((classModel) => {
    classModel.parent_classes?.forEach((parentIri) => {
      const edge: GraphEdge = {
        id: `inheritance-${classModel.uri}-${parentIri}`,
        source: classModel.uri, // Child class (specialized)
        target: parentIri,      // Parent class (generic)
        type: 'smoothstep',
        data: { isInheritance: true },
        style: { stroke: '#94a3b8', strokeWidth: 3, strokeDasharray: '5,5' },
        markerEnd: {
          type: 'arrowclosed',
          color: '#94a3b8',
        },
      };
      edges.push(edge);
    });
  });

  // Create edges for relationships
  ontology.relationships?.forEach((rel, index) => {
    const edge: GraphEdge = {
      id: `rel-${index}`,
      source: rel.domain_class,
      target: rel.range_class,
      label: rel.label,
      type: 'smoothstep',
      data: { relationship: rel },
      style: { stroke: '#3b82f6', strokeWidth: 3 },
      markerEnd: {
        type: 'arrowclosed',
        color: '#3b82f6',
      },
      labelStyle: { fill: '#1e40af', fontWeight: 600, fontSize: 12 },
      labelBgStyle: { fill: '#fff', fillOpacity: 0.9 },
    };
    edges.push(edge);
  });

  console.log('🔍 Graph Data:', {
    nodeCount: nodes.length,
    edgeCount: edges.length,
    inheritanceEdges: edges.filter(e => e.data?.isInheritance).length,
    relationshipEdges: edges.filter(e => e.data?.relationship).length,
    sampleEdges: edges.slice(0, 3),
  });

  return { nodes, edges };
}

/**
 * Apply Dagre hierarchical layout to position nodes
 */
export function applyDagreLayout(
  nodes: GraphNode[],
  edges: GraphEdge[],
  direction: 'TB' | 'LR' = 'TB'
): GraphNode[] {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  // Configure layout
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 100,
    ranksep: 150,
    marginx: 50,
    marginy: 50,
  });

  // Add nodes to Dagre
  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });

  // Add edges to Dagre
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // Calculate layout
  dagre.layout(dagreGraph);

  // Apply positions to nodes
  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - NODE_WIDTH / 2,
        y: nodeWithPosition.y - NODE_HEIGHT / 2,
      },
    };
  });

  return layoutedNodes;
}

/**
 * Get initial layout with nodes and edges positioned
 */
export function getInitialGraphLayout(
  ontology: OntologyModel | null,
  direction: 'TB' | 'LR' = 'TB'
): {
  nodes: GraphNode[];
  edges: GraphEdge[];
} {
  const { nodes, edges } = buildGraphData(ontology);
  const layoutedNodes = applyDagreLayout(nodes, edges, direction);
  return { nodes: layoutedNodes, edges };
}
