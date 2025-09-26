<script setup>
// import { useRoute } from 'vue-router'
import { ref, onMounted, onBeforeUnmount, reactive, watch } from "vue";

import * as monaco from "monaco-editor/esm/vs/editor/editor.api";
import { ClickOutside as vClickOutside } from 'element-plus';
import JsMark from "js-mark";
import "vue-diff/dist/index.css";
import {exportJson,importJson,filesname} from "@/api/api";
import diffEditor from "@/components/diffEditor.vue";

// import { useStore } from 'vuex';
// let { proxy } = getCurrentInstance();
// const store = useStore()
// const route = useRoute()
import { diffChars } from "diff";
import { html as diff2html } from "diff2html";
import "diff2html/bundles/css/diff2html.min.css";

import Sortable from 'sortablejs';




 
const items = ref([
  { id: 1, name: '苹果' },
  { id: 2, name: '香蕉' },
  { id: 3, name: '橙子' }
]);
 
const listRef = ref(null);
 
onMounted(() => {
  if (listRef.value) {
    new Sortable(listRef.value, {
      animation: 150,
      onEnd: (event) => {
        const movedItem = items.value.splice(event.oldIndex, 1)[0];
        items.value.splice(event.newIndex, 0, movedItem);
        console.log(items.value);
      }
    });
  }
});





const str = ref(localStorage.getItem('COMMON__MARKDOWN_EDITOR__TEXT') || '')







</script>

<template>
<div class="pagebox">
  <div style="width: 100%;height: 800px;">
  <v-md-editor height="800px" style="width: 100%;" v-model="str"></v-md-editor>
</div>
</div>


  <!-- <diffEditor style="height: calc(100% - 500px);" :newval="a" :oldval="a1" v-model="isShowdiffEditor"></diffEditor> -->
</template>

<style scoped>
.pagebox{
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  width: 100%;
  height: 100%;
}

.pagebox .lbox{
  display: block;
  width: 30%;
  height: 100%;
}
.pagebox .rbox{
  display: block;
  width: 70%;
  height: 100%;
}
</style>
