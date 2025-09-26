<script setup>
// import { useRoute } from 'vue-router'
import { ref, onMounted, onBeforeUnmount, reactive, watch } from "vue";

import * as monaco from "monaco-editor/esm/vs/editor/editor.api";

import "vue-diff/dist/index.css";

const props = defineProps({

  newval: {type:String,
    default: () => {
      return ""
    }
  },
  oldval: {type:String,
    default: () => {
      return ""
    }
  },
  modelValue: { type: Boolean, default: false },
});

// import { useStore } from 'vuex';
// let { proxy } = getCurrentInstance();
// const store = useStore()
// const route = useRoute()


onMounted(() => {
  setTimeout(() => {
    initEditor();
  }, 70);
  
});



const isShowdiffEditor = ref(false);

const editorContainer = ref(null);
let editorInstance = null;

let originalModel;
let modifiedModel;

let defopt = {
  value: "",
  theme: "vs", // 编辑器主题：vs, hc-black, or vs-dark，更多选择详见官网
  roundedSelection: false, // 右侧不显示编辑器预览框
  autoIndent: true, // 自动缩进
  readOnly: false, // 是否只读
  diffWordWrap: "on",  //描述：是否在差异编辑器中启用单词换行可选项： "on" | "off" | "inherit"
  ignoreTrimWhitespace:true,  //描述：是否忽略差异编辑器中的空格。
  diffWordWrap: "on", //描述：是否在差异编辑器中启用单词换行可选项： "on" | "off" | "inherit"
  enableSplitViewResizing:true,  //描述：是否允许用户调整分割视图的大小
  originalEditable:true, //描述：是否允许用户编辑原始编辑器的内容
  renderIndicators: true, //是否在差异编辑器中渲染指示器
  acceptSuggestionOnCommitCharacter:false,  //描述：是否在差异编辑器中启用Tab键接受建议
  roundedSelection: false, // 右侧不显示编辑器预览框
  automaticLayout:true, //描述: 用于控制是否自动调整编辑器的大小 如果将 automaticLayout 设置为 true ，则编辑器会在窗口大小发生变化时自动调整大小以适应新的窗口大小
  bracketPairColorization:true, //描述: 用于控制是否高亮显示匹配的括号 如果将 bracketPairColorization 设置为 true ，则编辑器会在输入左括号时高亮显示相应的右括号，并在将光标放在左括号或右括号上时高亮显示相应的匹配括号。

  contextmenu:false,  //描述: 控制是否启用上下文菜单。
  autoIndent: true, // 自动缩进
  diffWordWrap:true,
  wordWrap:'on',
  automaticLayout:true,
  scrollBeyondLastLine:false,
  scrollbar:{
    verticalScrollbarSize: 0
  },
};
const newval = `function add(a,v, b) { return a + b; }{
  "ids": [
    "1134_1_6",
    "1134_1_2",
    "knowledge_document_215_2",
    "1134_1_4",
    "knowledge_document_215_3",
    "knowledge_document_215_1"
  ],
  "ids2": [],
  "ids3": [],
  "ids4": [
    "1134_1_6",
    "1134_1_2",
    "1134_1_4",
    "knowledge_document_215_2",
    "knowledge_document_215_1",
    "knowledge_document_215_3"
  ]
}`
const oldval = `function add(a, b) { return a + b; }{
  "ids": [
    "1134_1_6",
    "1134_1_2",
    "knowledge_document_215_2",
    "1134_1_4",
    "knowledge_document_225_3",
    "knowledge_document_215_1"
  ],
  "ids2": [],
  "ids3": [],
  "ids4": [
    "1134_1_6",
    "1134_1_2",
    "1134_1_4",
    "knowledge_document_225_2",
    "knowledge_document_215_1",
    "knowledge_document_215_3"
  ]
}`
const initEditor = () => {
  editorInstance = monaco.editor.createDiffEditor(
    editorContainer.value,
    defopt
  );
  originalModel = monaco.editor.createModel(
    newval,
    "text/plain"
  );
  modifiedModel = monaco.editor.createModel(
    oldval,
    "text/plain"
  );

  editorInstance.setModel({
    original: originalModel,
    modified: modifiedModel,
  });
};

onBeforeUnmount(() => {
  editorInstance.dispose();
});
</script>

<template>
  <!-- <el-button @click="isShowdiffEditor = true">对比文本</el-button> -->
  <div style="width: 100%; height: calc(100% - 1px)">
    <div class="editor-containbox nodrag nowheel">
      <div
        ref="editorContainer"
        class="editor-container c-scroll-contain"
      ></div>
    </div>
  </div>


</template>

<style scoped>
.editor-containbox {
  display: block;
  width: 100%;
  height: 100%;
  position: relative;
  padding: 5px 0;
  box-sizing: border-box;
  border: 1px solid var(--el-border-color);
  border-radius: 5px;
  z-index: 11;
}
.editor-containbox :deep(.monaco-editor .line-delete, .monaco-diff-editor .line-delete){
  background-color:rgb(243 12 12 / 17%);
}

.editor-containbox :deep(.monaco-editor .char-delete, .monaco-diff-editor .char-delete){
  background-color: rgb(243 12 12 / 30%);
}
.editor-containbox :deep(.monaco-editor .line-insert, .monaco-diff-editor .line-insert){
  background-color: rgba(130, 255, 80,0.2);
}
.editor-containbox :deep(.monaco-editor .char-insert, .monaco-diff-editor .char-insert){
  background-color: rgba(130, 255, 80,0.5);
}

.editor-container {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  text-align: left;
  font-size: 12px;
  position: relative;
  z-index: 1;
}
.diff {
  text-align: left;
  padding: 20px;
}
.diff :deep(.removed) {
  background: var(--el-color-danger);
}
.diff :deep(.row) {
  display: block;
  line-height: 22px;
}
.diff :deep(.row.off) {
  background: #fdeaea;
}
.diff :deep(.row.on) {
  background: #eafdf5;
}

.diff :deep(.added) {
  background: var(--el-color-success);
}
</style>
