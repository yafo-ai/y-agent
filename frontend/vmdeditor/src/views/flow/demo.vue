
<!-- =======================设置子节点 -->

<!-- <script setup>
 
import { ref } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'

const nodes = ref([
  {
    id: '1',
    type: 'input',
    data: { label: 'node' },
    position: { x: 250, y: 0 },
  },
  {
    id: '2',
    data: { label: 'parent node' },
    position: { x: 100, y: 100 },
    style: { backgroundColor: 'rgba(16, 185, 129, 0.5)', width: '200px', height: '200px' },
  },
  {
    id: '2a',
    data: { label: 'child node' },
    position: { x: 10, y: 50 },
    parentNode: '2',
  },
  {
    id: '4',
    data: { label: 'parent node' },
    position: { x: 320, y: 175 },
    style: { backgroundColor: 'rgba(16, 185, 129, 0.5)', width: '400px', height: '300px' },
  },
  {
    id: '4a',
    data: { label: 'child node' },
    position: { x: 15, y: 65 },
    extent: 'parent',
    parentNode: '4',
  },
  {
    id: '4b',
    data: { label: 'nested parent node' },
    position: { x: 15, y: 120 },
    style: { backgroundColor: 'rgba(139, 92, 246, 0.5)', height: '150px', width: '270px' },
    parentNode: '4',
  },
  {
    id: '4b1',
    data: { label: 'nested child node' },
    position: { x: 20, y: 40 },
    parentNode: '4b',
  },
  {
    id: '4b2',
    data: { label: 'nested child node' },
    position: { x: 100, y: 100 },
    parentNode: '4b',
  },
  {
    id: '4c',
    data: { label: 'child node' },
    position: { x: 200, y: 65 },
    parentNode: '4',
  },
  {
    id: '999',
    type: 'input',
    data: { label: 'Drag me to extend area!' },
    position: { x: 20, y: 100 },
    class: 'light',
    expandParent: true,
    parentNode: '2',
  },
])

const edges = ref([
  { id: 'e1-2', source: '1', target: '2' },
  { id: 'e1-4', source: '1', target: '4' },
  { id: 'e1-4c', source: '1', target: '4c' },
  { id: 'e2a-4a', source: '2a', target: '4a' },
  { id: 'e4a-4b1', source: '4a', target: '4b1' },
  { id: 'e4a-4b2', source: '4a', target: '4b2' },
  { id: 'e4b1-4b2', source: '4b1', target: '4b2' },
])
</script>

<template>
  <VueFlow :nodes="nodes" :edges="edges" fit-view-on-init elevate-edges-on-select>
    <MiniMap />

    <Controls />

    <Background />
  </VueFlow>
</template> 









-->



<!-- =======================判断节点是否相交 -->

<script setup>
import { computed, ref } from 'vue'
import { Panel, VueFlow, useVueFlow } from '@vue-flow/core'

/**
 * You can either use `getIntersectingNodes` to check if a given node intersects with others
 * or `isNodeIntersecting` to check if a node is intersecting with a given area
 */
const { onNodeDrag, getIntersectingNodes, isNodeIntersecting, updateNode, screenToFlowCoordinate } = useVueFlow()

const nodes = ref([
  {
    id: '1',
    data: { label: 'Node 1' },
    position: { x: 0, y: 0 },
  },
  {
    id: '2',
    data: { label: 'Node 2' },
    position: { x: 400, y: 400 },
  },
  {
    id: '3',
    data: { label: 'Node 3' },
    position: { x: 400, y: 0 },
  },
  {
    id: '4',
    data: { label: 'Node 4' },
    position: { x: 0, y: 400 },
  },
  {
    id: '5',
    style: { borderColor: 'red' },
    data: { label: 'Drag me  over another node' },
    position: { x: 200, y: 200 },
  },
])

const panelEl = ref()

const isIntersectingWithPanel = ref(false)

const panelPosition = computed(() => {
  if (!panelEl.value) {
    return {
      x: 0,
      y: 0,
      width: 0,
      height: 0,
    }
  }

  const { left, top, width, height } = panelEl.value.$el.getBoundingClientRect()

  return {
    ...screenToFlowCoordinate({ x: left, y: top }),
    width,
    height,
  }
})

onNodeDrag(({ node: draggedNode }) => {
  const intersections = getIntersectingNodes(draggedNode)
  const intersectionIds = intersections.map((intersection) => intersection.id)

  isIntersectingWithPanel.value = isNodeIntersecting(draggedNode, panelPosition.value)

  for (const node of nodes.value) {
    const isIntersecting = intersectionIds.includes(node.id)

    updateNode(node.id, { class: isIntersecting ? 'intersecting' : '' })
  }
})
</script>

<template>
  <VueFlow :nodes="nodes" fit-view-on-init>
    <Panel ref="panelEl" position="bottom-right" :class="{ intersecting: isIntersectingWithPanel }"> </Panel>
  </VueFlow>
</template>





