# Ontology Changes Filtering - Design Analysis

## Requirement
Users need to filter the ontology view to show **only changed elements** after applying an iteration.

## Challenge
For relationships and inheritance, we must show the connected classes even if they weren't changed, otherwise the relationships would be meaningless.

## Proposed Solution

### Filter Mode Options

Add a filter dropdown/toggle with three modes:

1. **All Elements** (default)
   - Shows the complete ontology
   - Highlights changes if "Show Changes" is checked

2. **Changed Elements Only** 
   - Shows only elements that were directly changed
   - For relationships/inheritance: also shows their connected classes
   - This creates a "change-focused subgraph"

3. **Changed + 1-Hop** (optional enhancement)
   - Shows changed elements
   - Plus all elements directly connected to changed elements
   - Provides more context

### Implementation Strategy

#### Data Layer: Compute Changed Element Sets

```typescript
interface FilteredOntologyData {
  // Elements that were directly changed
  changedClasses: Set<string>  // URIs
  changedAttributes: Set<string>
  changedRelationships: Set<string>
  
  // Classes needed to display changed relationships/inheritance
  requiredClasses: Set<string>  // URIs of classes needed as endpoints
  
  // Final sets to display
  visibleClasses: Set<string>
  visibleAttributes: Set<string>
  visibleRelationships: Set<string>
}
```

#### Algorithm

```typescript
function computeFilteredElements(
  ontology: OntologyModel,
  changes: OntologyChanges
): FilteredOntologyData {
  
  // 1. Direct changes
  const changedClasses = new Set(changes.classes.keys())
  const changedAttributes = new Set(changes.attributes.keys())
  const changedRelationships = new Set(changes.relationships.keys())
  
  // 2. Find required classes (endpoints of changed relationships/inheritance)
  const requiredClasses = new Set<string>()
  
  // Add classes needed for changed relationships
  ontology.relationships?.forEach(rel => {
    if (changedRelationships.has(rel.uri)) {
      requiredClasses.add(rel.domain_class)
      requiredClasses.add(rel.range_class)
    }
  })
  
  // Add classes needed for changed inheritance
  // Check both directions: child->parent and parent->child
  ontology.classes?.forEach(cls => {
    // If this class changed and has parents, include parents
    if (changedClasses.has(cls.uri) && cls.parent_classes) {
      cls.parent_classes.forEach(parentUri => {
        requiredClasses.add(parentUri)
      })
    }
    
    // If this class has changed children, include this class
    const hasChangedChildren = ontology.classes?.some(child =>
      changedClasses.has(child.uri) && 
      child.parent_classes?.includes(cls.uri)
    )
    if (hasChangedChildren) {
      requiredClasses.add(cls.uri)
    }
  })
  
  // 3. Combine: changed + required
  const visibleClasses = new Set([
    ...changedClasses,
    ...requiredClasses
  ])
  
  // 4. Filter attributes: only those belonging to visible classes
  const visibleAttributes = new Set<string>()
  ontology.attributes?.forEach(attr => {
    if (changedAttributes.has(attr.uri) && visibleClasses.has(attr.domain_class)) {
      visibleAttributes.add(attr.uri)
    }
  })
  
  // 5. Relationships: only changed ones (classes already included above)
  const visibleRelationships = new Set(changedRelationships)
  
  return {
    changedClasses,
    changedAttributes,
    changedRelationships,
    requiredClasses,
    visibleClasses,
    visibleAttributes,
    visibleRelationships
  }
}
```

### UI Components

#### Filter Control (in OntologyPage toolbar)

```tsx
<select 
  value={filterMode}
  onChange={(e) => setFilterMode(e.target.value)}
  className="border rounded-card px-3 py-2"
  disabled={!changes} // Only enabled when changes exist
>
  <option value="all">All Elements</option>
  <option value="changed">Changed Only</option>
</select>
```

#### Visual Indicators

When in "Changed Only" mode:
- **Required classes** (shown as endpoints): Display with a subtle visual indicator
  - Light gray border or background
  - Small badge: "Connected"
  - Tooltip: "Shown as endpoint of changed relationship"

- **Changed elements**: Keep existing highlighting (green/yellow/red)

### View-Specific Implementation

#### Grid View
- Filter rows based on `visibleClasses`, `visibleAttributes`, `visibleRelationships`
- Group by element type with headers showing counts
- Example: "Classes (5 changed + 3 connected)"

#### Graph View
- Filter nodes to `visibleClasses`
- Filter edges to show:
  - Changed relationships (from `visibleRelationships`)
  - Inheritance between visible classes where inheritance changed
- Use React Flow's node/edge filtering

#### Force View
- Filter nodes to `visibleClasses`
- Filter edges similarly to Graph view
- Rebuild force simulation with filtered data

### Edge Cases

1. **Deleted elements**: 
   - Show with special styling (faded, crossed out)
   - In relationships: "Class A → [DELETED: Class B]"

2. **Orphaned attributes**:
   - If attribute changed but its class is not visible, should we show it?
   - **Recommendation**: No - attributes without their class context are not useful

3. **Isolated classes**:
   - Changed class with no relationships shown
   - **Recommendation**: Still show - the class itself is the change

4. **Chain inheritance**:
   - A → B → C, if B changes
   - Show A, B, C? Or just B and its direct parents/children?
   - **Recommendation**: Only direct connections (B's parents and children)

### Performance Considerations

- Compute filtered sets in useMemo()
- Cache results until changes or ontology update
- For large ontologies, consider indexing

### Alternative: Dimming Instead of Filtering

Instead of hiding unchanged elements, we could:
- Show all elements but **dim** the unchanged ones
- Changed elements: Normal styling + highlights
- Required elements: Normal styling, no highlights  
- Unchanged elements: 50% opacity + grayscale

**Pros:**
- User keeps full context
- No confusion about "missing" elements
- Easier to implement

**Cons:**
- Large ontologies still cluttered
- Less focus on changes

## Recommendation

**Implement the filtering approach** with these features:

1. **Filter Mode Selector**:
   - "All Elements" (default)
   - "Changed Elements Only"

2. **Smart Inclusion Rules**:
   - Show all changed elements
   - Show required endpoint classes for relationships/inheritance
   - Mark required classes differently than changed ones

3. **Visual Distinction**:
   - Changed elements: Bold highlight (green/yellow/red)
   - Required elements: Subtle indicator (light border, small badge)
   - Clear legend explaining the difference

4. **Grid View Enhancement**:
   - Group by type with counts
   - "5 classes changed, 3 classes shown as endpoints"

5. **Future Enhancement**:
   - Add "Changed + Connected" mode showing 1-hop neighborhood
   - Add "Dim Unchanged" mode as alternative to filtering

## Implementation Plan

### Phase 1: Data Layer
1. Add `filterMode` to store or local state
2. Implement `computeFilteredElements()` function
3. Add filtering logic to all three view components

### Phase 2: UI
1. Add filter mode selector to toolbar
2. Add visual indicators for required vs changed elements
3. Update stats to show filtered counts

### Phase 3: Refinement
1. Add tooltips explaining why elements are shown
2. Add legend/help text
3. Performance optimization for large ontologies

Would you like me to proceed with implementing this solution?
