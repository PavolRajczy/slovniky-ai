/**
 * OntologyForceGraph - Force-directed graph visualization for ontology
 * 
 * Features:
 * - Interactive force-directed layout using D3.js
 * - Canvas-based rendering for performance
 * - Persistent node positions (survives page refresh!)
 * 
 * User Interactions:
 * - **Drag nodes**: Move and auto-pin nodes to desired positions
 * - **Right-click nodes**: Unpin nodes to let them move freely again
 * - **Click nodes**: Select a class to view details
 * - **Zoom/Pan**: Mouse wheel to zoom, drag background to pan
 * 
 * Position Persistence:
 * - Pinned positions are stored in browser localStorage
 * - Positions persist across view switches, filter changes, and page refreshes
 * - Positions are scoped per project (switching projects loads different layout)
 * - Old positions (30+ days) are automatically cleaned up
 */

import React, { useEffect, useRef, useState } from 'react';
import { OntologyModel, OntologyClassModel, OntologyAttributeModel } from '../lib/api';
import { buildGraphData } from '../lib/ontologyGraphLayout';
import { OntologyCanvas } from '../lib/OntologyCanvas';
import { OntologyChanges, ChangeType, FilteredElements } from '@/store/ontologyChangesStore';
import { useNodePositionsStore } from '@/store/nodePositionsStore';
import { useProjectStore } from '@/store/projectStore';

export type SelectedElement =
  | { type: 'class'; uri: string }
  | { type: 'attribute'; uri: string }
  | { type: 'relationship'; uri: string }
  | null;

interface OntologyForceGraphProps {
  ontology: OntologyModel | null;
  selectedElement: SelectedElement;
  onSelectClass: (uri: string) => void;
  changes?: OntologyChanges | null;
  filteredElements?: FilteredElements | null;
}

export const OntologyForceGraph: React.FC<OntologyForceGraphProps> = ({
  ontology,
  selectedElement,
  onSelectClass,
  changes,
  filteredElements,
}) => {
  const { projectId } = useProjectStore();
  const { pinNode, unpinNode, getProjectPositions } = useNodePositionsStore();
  
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<OntologyCanvas | null>(null);
  const [selectedAttribute, setSelectedAttribute] = useState<OntologyAttributeModel | null>(null);

  // Get selected class details
  const selectedClass = selectedElement?.type === 'class' 
    ? ontology?.classes?.find(c => c.uri === selectedElement.uri)
    : null;

  // Get attributes for selected class
  const classAttributes = selectedClass
    ? ontology?.attributes?.filter(attr => attr.domain_class === selectedClass.uri) || []
    : [];

  // Initialize canvas on mount
  useEffect(() => {
    if (!containerRef.current || !projectId) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Create canvas instance with pin callbacks
    const canvas = new OntologyCanvas(
      container, 
      width, 
      height, 
      onSelectClass,
      // onNodePin callback - save position to store
      (nodeUri, x, y) => {
        pinNode(projectId, nodeUri, x, y);
        console.log('📌 Pinned node:', nodeUri, 'at', { x, y });
      },
      // onNodeUnpin callback - remove position from store
      (nodeUri) => {
        unpinNode(projectId, nodeUri);
        console.log('📍 Unpinned node:', nodeUri);
      }
    );
    
    canvasRef.current = canvas;

    // Cleanup on unmount
    return () => {
      canvas.destroy();
      canvasRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]); // Re-initialize if project changes

  // Load data when ontology, changes, or filteredElements change
  useEffect(() => {
    if (!canvasRef.current || !ontology || !projectId) return;

    let { nodes, edges } = buildGraphData(ontology);
    
    // Apply filtering if filteredElements is available
    if (filteredElements) {
      nodes = nodes.filter(node => 
        filteredElements.visibleClasses.has(node.data.classModel.uri)
      );
      edges = edges.filter(edge => {
        // Filter relationship edges
        if (edge.data?.relationship) {
          return filteredElements.visibleRelationships.has(edge.data.relationship.uri);
        }
        // Filter inheritance edges
        if (edge.data?.isInheritance) {
          const key = `${edge.source}->${edge.target}`;
          return filteredElements.visibleInheritances.has(key);
        }
        return true;
      });
    }
    
    // Add change information to nodes if available
    if (changes) {
      nodes.forEach(node => {
        const changeType = changes.classes.get(node.id);
        if (changeType) {
          node.data = {
            ...node.data,
            changeType,
          };
        }
      });
      
      // Add change information to edges
      edges.forEach(edge => {
        const isInheritance = edge.data?.isInheritance || false;
        let changeType = null;
        
        if (isInheritance) {
          changeType = changes.inheritances.get(`${edge.source}->${edge.target}`);
        } else if (edge.data?.relationship) {
          // For relationships, use the relationship URI from the data
          const relUri = edge.data.relationship.uri;
          changeType = changes.relationships.get(relUri);
          
          // Debug logging
          if (changeType) {
            console.log('⚡ Force View - Found relationship change:', {
              edgeId: edge.id,
              relationshipUri: relUri,
              changeType,
              label: edge.label,
            });
          }
        }
        
        if (changeType && edge.data) {
          edge.data = {
            ...edge.data,
            changeType,
          };
        }
      });
    }
    
    // Get pinned positions for this project
    const pinnedPositions = getProjectPositions(projectId);
    console.log(`📍 Restoring ${pinnedPositions.size} pinned positions for project ${projectId}`);
    
    canvasRef.current.loadData(nodes, edges, pinnedPositions);
  }, [ontology, changes, filteredElements, projectId, getProjectPositions]);

  // Update selection when selectedElement changes
  useEffect(() => {
    if (!canvasRef.current) return;

    if (selectedElement?.type === 'class') {
      canvasRef.current.setSelectedNode(selectedElement.uri);
    } else {
      canvasRef.current.setSelectedNode(null);
    }
    
    // Clear attribute selection when class changes
    setSelectedAttribute(null);
  }, [selectedElement]);

  if (!ontology) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No ontology data available
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      <div ref={containerRef} className="w-full h-full" />
      
      {/* Instructions overlay */}
      <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-md p-3 text-xs text-gray-600 max-w-xs">
        <div className="font-semibold mb-1">Controls:</div>
        <ul className="space-y-0.5">
          <li>• <strong>Drag</strong> nodes to reposition & pin</li>
          <li>• <strong>Right-click</strong> pinned node to unpin</li>
          <li>• <strong>Mouse wheel</strong> to zoom</li>
          <li>• <strong>Click</strong> node to select</li>
          <li>• <strong>Drag background</strong> to pan</li>
        </ul>
        <div className="mt-2 pt-2 border-t border-gray-200">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-0.5 bg-blue-500"></div>
            <span>Relationships</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-gray-400" style={{ borderTop: '2px dashed #94a3b8' }}></div>
            <span>Inheritance</span>
          </div>
        </div>
      </div>

      {/* Class Details Panel */}
      {selectedClass && (
        <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-md p-4 text-sm max-w-md max-h-[calc(100vh-8rem)] overflow-y-auto">
          <div className="mb-3">
            <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Class</div>
            <div className="font-bold text-gray-900 text-base mb-2">{selectedClass.label}</div>
            
            {selectedClass.definition && (
              <div className="mb-2">
                <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Definition</div>
                <div className="text-gray-700 text-xs">{selectedClass.definition}</div>
              </div>
            )}
            
            {selectedClass.description && (
              <div className="mb-2">
                <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Description</div>
                <div className="text-gray-700 text-xs">{selectedClass.description}</div>
              </div>
            )}
          </div>

          {classAttributes.length > 0 && (
            <div className="border-t border-gray-200 pt-3">
              <div className="text-xs text-gray-500 uppercase font-semibold mb-2">
                Attributes ({classAttributes.length})
              </div>
              <ul className="space-y-1">
                {classAttributes.map(attr => (
                  <li
                    key={attr.uri}
                    onClick={() => setSelectedAttribute(attr)}
                    className={`
                      px-2 py-1.5 rounded cursor-pointer transition-colors text-xs
                      ${selectedAttribute?.uri === attr.uri 
                        ? 'bg-blue-100 text-blue-900 font-semibold' 
                        : 'hover:bg-gray-100 text-gray-700'
                      }
                    `}
                  >
                    {attr.label}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Attribute Details Panel */}
      {selectedAttribute && (
        <div className="absolute top-4 left-4 ml-[calc(28rem)] bg-white/90 backdrop-blur-sm rounded-lg shadow-md p-4 text-sm max-w-md">
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1">
              <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Attribute</div>
              <div className="font-bold text-gray-900 text-base mb-2">{selectedAttribute.label}</div>
            </div>
            <button
              onClick={() => setSelectedAttribute(null)}
              className="ml-2 text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close attribute details"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {selectedAttribute.definition && (
            <div className="mb-3">
              <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Definition</div>
              <div className="text-gray-700 text-xs">{selectedAttribute.definition}</div>
            </div>
          )}

          {selectedAttribute.description && (
            <div className="mb-3">
              <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Description</div>
              <div className="text-gray-700 text-xs">{selectedAttribute.description}</div>
            </div>
          )}

          <div className="border-t border-gray-200 pt-3 space-y-2">
            <div>
              <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Domain</div>
              <div className="text-gray-700 text-xs font-mono bg-gray-50 px-2 py-1 rounded">
                {ontology?.classes?.find(c => c.uri === selectedAttribute.domain_class)?.label || selectedAttribute.domain_class}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Range Type</div>
              <div className="text-gray-700 text-xs font-mono bg-gray-50 px-2 py-1 rounded">
                {selectedAttribute.range_type}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
