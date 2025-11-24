import React, { useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  NodeProps,
  useNodesState,
  useEdgesState,
  NodeTypes,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { OntologyModel, OntologyAttributeModel } from '../lib/api';
import { getInitialGraphLayout, GraphNode } from '../lib/ontologyGraphLayout';
import { OntologyChanges, ChangeType, FilteredElements } from '@/store/ontologyChangesStore';
import { getClassDisplayType } from '@/lib/ontologyFiltering';

export type SelectedElement =
  | { type: 'class'; uri: string }
  | { type: 'attribute'; uri: string }
  | { type: 'relationship'; uri: string }
  | null

interface OntologyGraphProps {
  ontology: OntologyModel | null;
  selectedElement: SelectedElement;
  onSelectClass: (uri: string) => void;
  changes?: OntologyChanges | null;
  filteredElements?: FilteredElements | null;
}

// Custom Class Node Component (UML-style)
const ClassNode: React.FC<NodeProps> = ({ data, selected }) => {
  const { label, attributes, childCount, relationshipCount, changeType } = data as {
    label: string;
    attributes: OntologyAttributeModel[];
    childCount: number;
    relationshipCount: number;
    changeType?: ChangeType | null;
  };

  // Show max 5 attributes, then "..."
  const maxAttributes = 5;
  const displayAttributes = attributes.slice(0, maxAttributes);
  const hasMore = attributes.length > maxAttributes;

  // Get border color based on change type
  const getBorderColor = () => {
    if (selected) return 'border-blue-500';
    if (!changeType) return 'border-gray-300';
    switch (changeType) {
      case 'created':
        return 'border-green-500';
      case 'modified':
        return 'border-yellow-500';
      case 'deleted':
        return 'border-red-500';
      default:
        return 'border-gray-300';
    }
  };

  // Get background color for header based on change type
  const getHeaderBgColor = () => {
    if (!changeType) return 'bg-gray-50';
    switch (changeType) {
      case 'created':
        return 'bg-green-50';
      case 'modified':
        return 'bg-yellow-50';
      case 'deleted':
        return 'bg-red-50';
      default:
        return 'bg-gray-50';
    }
  };

  // Get change badge
  const getChangeBadge = () => {
    if (!changeType) return null;
    switch (changeType) {
      case 'created':
        return <span className="text-[10px] font-bold text-green-700 bg-green-100 px-1.5 py-0.5 rounded">NEW</span>;
      case 'modified':
        return <span className="text-[10px] font-bold text-yellow-700 bg-yellow-100 px-1.5 py-0.5 rounded">MOD</span>;
      case 'deleted':
        return <span className="text-[10px] font-bold text-red-700 bg-red-100 px-1.5 py-0.5 rounded">DEL</span>;
    }
  };

  return (
    <>
      {/* Connection handles for React Flow edges */}
      <Handle
        type="target"
        position={Position.Top}
        style={{ background: '#6b7280', width: 8, height: 8 }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: '#6b7280', width: 8, height: 8 }}
      />
      
      <div
        className={`rounded-lg border-2 bg-white shadow-md transition-all ${
          selected
            ? 'border-blue-500 shadow-lg ring-2 ring-blue-200'
            : `${getBorderColor()} hover:border-blue-300 hover:shadow-lg`
        } ${changeType === 'deleted' ? 'opacity-60' : ''}`}
        style={{ minWidth: '250px', maxWidth: '350px' }}
      >
        {/* Class Name Header */}
        <div className={`px-4 py-2 ${getHeaderBgColor()} border-b border-gray-300 rounded-t-lg`}>
          <div className="font-bold text-gray-900 text-sm text-center flex items-center justify-center gap-2">
            <span>{label}</span>
            {getChangeBadge()}
          </div>
        </div>

        {/* Attributes Section */}
        {attributes.length > 0 && (
          <div className="px-3 py-2 border-b border-gray-200">
            {displayAttributes.map((attr, idx) => (
              <div
                key={attr.uri}
                className="text-xs text-gray-700 py-0.5 font-mono"
                title={attr.definition || attr.description || attr.label}
              >
                • {attr.label}
                {attr.range_type && (
                  <span className="text-gray-500">: {attr.range_type}</span>
                )}
              </div>
            ))}
            {hasMore && (
              <div className="text-xs text-gray-400 italic py-0.5">
                ... and {attributes.length - maxAttributes} more
              </div>
            )}
          </div>
        )}

        {/* Stats Footer */}
        <div className="px-3 py-1.5 bg-gray-50 rounded-b-lg flex gap-3 text-xs text-gray-500">
          {relationshipCount > 0 && (
            <span>
              <span className="font-medium">{relationshipCount}</span> rel
            </span>
          )}
          {childCount > 0 && (
            <span>
              <span className="font-medium">{childCount}</span> sub
            </span>
          )}
        </div>
      </div>
    </>
  );
};

const nodeTypes: NodeTypes = {
  classNode: ClassNode,
};

export const OntologyGraph: React.FC<OntologyGraphProps> = ({
  ontology,
  selectedElement,
  onSelectClass,
  changes,
  filteredElements,
}) => {
  // Build initial graph layout
  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => {
      const layout = getInitialGraphLayout(ontology, 'TB');
      
      // Filter nodes/edges based on filteredElements
      if (filteredElements) {
        layout.nodes = layout.nodes.filter(node => 
          filteredElements.visibleClasses.has(node.data.classModel.uri)
        )
        layout.edges = layout.edges.filter(edge => {
          // Filter relationship edges
          if (edge.data?.relationship) {
            return filteredElements.visibleRelationships.has(edge.data.relationship.uri)
          }
          // Filter inheritance edges
          if (edge.data?.isInheritance) {
            const key = `${edge.source}->${edge.target}`
            return filteredElements.visibleInheritances.has(key)
          }
          return true
        })
      }
      
      // Add change information to nodes
      if (changes) {
        layout.nodes = layout.nodes.map(node => ({
          ...node,
          data: {
            ...node.data,
            changeType: changes.classes.get(node.id) || null,
          },
        }));
        
        // Add change styling to edges
        layout.edges = layout.edges.map(edge => {
          const isInheritance = edge.data?.isInheritance || false;
          let changeType: any = null;
          
          if (isInheritance) {
            changeType = changes.inheritances.get(`${edge.source}->${edge.target}`);
          } else if (edge.data?.relationship) {
            // For relationships, use the relationship URI from the data
            const relUri = edge.data.relationship.uri;
            changeType = changes.relationships.get(relUri);
            
            // Debug logging
            if (changeType) {
              console.log('📊 Graph View - Found relationship change:', {
                edgeId: edge.id,
                relationshipUri: relUri,
                changeType,
                label: edge.label,
              });
            }
          }
          
          if (changeType) {
            const style = edge.style ? { ...edge.style } : {};
            const animated = changeType === 'created';
            
            switch (changeType) {
              case 'created':
                style.stroke = '#22c55e'; // green
                style.strokeWidth = 3;
                break;
              case 'modified':
                style.stroke = '#eab308'; // yellow
                style.strokeWidth = 3;
                break;
              case 'deleted':
                style.stroke = '#ef4444'; // red
                style.strokeWidth = 3;
                style.opacity = 0.5;
                break;
            }
            
            return { ...edge, style, animated };
          }
          
          return edge;
        });
      }
      
      return layout;
    },
    [ontology, changes]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Debug: Log what we're rendering
  React.useEffect(() => {
    const nodeIds = new Set(nodes.map(n => n.id));
    const edgeIssues = edges.filter(e => !nodeIds.has(e.source) || !nodeIds.has(e.target));
    
    console.log('📊 OntologyGraph rendering:', {
      nodesCount: nodes.length,
      edgesCount: edges.length,
      sampleNodes: nodes.slice(0, 2).map(n => ({ id: n.id, label: n.data.label })),
      sampleEdges: edges.slice(0, 3).map(e => ({ 
        id: e.id, 
        source: e.source, 
        target: e.target, 
        label: e.label,
        type: e.type 
      })),
      edgesWithMissingNodes: edgeIssues.length,
      sampleMissingEdges: edgeIssues.slice(0, 2).map(e => ({
        edge: e.id,
        source: e.source,
        target: e.target,
        sourceExists: nodeIds.has(e.source),
        targetExists: nodeIds.has(e.target),
      })),
    });
  }, [nodes, edges]);

  // Update nodes when initial layout changes
  React.useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  // Update selected state when selectedElement changes
  React.useEffect(() => {
    if (selectedElement?.type === 'class') {
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          selected: node.id === selectedElement.uri,
        }))
      );
    } else {
      // Deselect all nodes if no class is selected
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          selected: false,
        }))
      );
    }
  }, [selectedElement, setNodes]);

  // Handle node click
  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      onSelectClass(node.id);
    },
    [onSelectClass]
  );

  if (!ontology) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No ontology data available
      </div>
    );
  }

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{
          padding: 0.2,
          minZoom: 0.1,
          maxZoom: 1.5,
        }}
        minZoom={0.05}
        maxZoom={2}
        defaultEdgeOptions={{
          type: 'smoothstep',
        }}
      >
        <Background color="#e5e7eb" gap={16} />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(node) => {
            if (node.selected) return '#3b82f6';
            return '#d1d5db';
          }}
          maskColor="rgba(0, 0, 0, 0.05)"
          style={{
            backgroundColor: '#f9fafb',
            border: '1px solid #e5e7eb',
          }}
        />
      </ReactFlow>
    </div>
  );
};
