<script setup>
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  useVueFlow,
} from "@vue-flow/core";
import { computed, ref } from "vue";

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
  sourceX: {
    type: Number,
    required: true,
  },
  sourceY: {
    type: Number,
    required: true,
  },
  targetX: {
    type: Number,
    required: true,
  },
  targetY: {
    type: Number,
    required: true,
  },
  sourcePosition: {
    type: String,
    required: true,
  },
  targetPosition: {
    type: String,
    required: true,
  },
  markerEnd: {
    type: String,
    required: false,
  },
  style: {
    type: Object,
    required: false,
  },
});
const { removeEdges, onEdgeMouseEnter, onEdgeMouseMove,onEdgeMouseLeave } = useVueFlow();

const curEdgeid = ref(null);

onEdgeMouseEnter((params) => {
  mouseent(params.edge.id);
});
let timermap = {};
onEdgeMouseLeave((params) => {
  mouselea(params.edge.id);
});
onEdgeMouseMove((params) => {
});
const mouselea = (id) => {
  clearTimeout(timermap[id]);
  timermap[id] = setTimeout(() => {
    let element = document.querySelector(".id-" + id);
    if(!element) return;
    element.style.display = "none";
    // document.querySelector("#" + id).parentNode.parentNode.style.zIndex = "110";
    document.querySelector(".icon-" + id).style.zIndex = "110";
  }, 1000);
};

const mouseent = (id,time) => {
  clearTimeout(timermap[id]);
  let timer = time || 0;
  setTimeout(() => {
    let element = document.querySelector(".id-" + id);
    if(!element) return;
    element.style.display = "block";
    // document.querySelector("#" + id).parentNode.parentNode.style.zIndex = "1010";
    document.querySelector(".icon-" + id).style.zIndex = "1111";
  }, timer);
};

const path = computed(() => getBezierPath(props));

const delfn = async (id) => {
  let cfm = await _this.$confirm("确定删除该链接？");
  if (!cfm) {
    return;
  }
  removeEdges(id);
};
</script>

<script>
export default {
  inheritAttrs: false,
};
</script>

<template>
  <!-- You can use the `BaseEdge` component to create your own custom edge more easily -->

  <BaseEdge
    class="c-edge"
    :id="id"
    :style="style"
    :path="path[0]"
    :marker-end="markerEnd"
  />

  <!-- Use the `EdgeLabelRenderer` to escape the SVG world of edges and render your own custom label in a `<div>` ctx -->
  <EdgeLabelRenderer>
    <div
      :style="{
        pointerEvents: 'all',
        position: 'absolute',
        transform: `translate(-50%, -50%) translate(${path[1]}px,${path[2]}px)`,
      }"
      :class="'nodrag nopan icon-' + id"
    >
      <span
        title="删除链接"
        @mouseenter="mouseent(id,1000)"
        @mouseleave="mouselea(id)"
        :class="
          'icon-del iconfont icon-cuowuguanbiquxiao-xianxingyuankuang id-' + id
        "
        @click="delfn(id)"
      ></span>
    </div>
  </EdgeLabelRenderer>
</template>
<style>
#arrow polyline,
body .vue-flow__edge-path,
body .vue-flow__connection-path {
  stroke: #165DFF !important;
  stroke-width: 2px;
}
</style>
<style coped>
.icon-del {
  cursor: pointer;
  display: block;
  width: 20px;
  line-height: 20px;
  height: 20px;
  border-radius: 100%;
  color: var(--el-color-danger);
  font-size: 18px;
  display: none;
  background: rgba(255, 255, 255, 0.95);
  transition: all 0.3s;
  z-index: 1011;
}
.icon-del:hover {
  display: block !important;
  color: #f00;
  font-weight: bold;
}
.edge-container {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}
</style>
