<script setup>
// import { useRoute } from 'vue-router'
import { ref, onMounted, onBeforeUnmount, reactive, watch } from "vue";

import * as monaco from "monaco-editor";
import JsMark from "js-mark";
import VueDiff from "vue-diff";
import "vue-diff/dist/index.css";

import diffEditor from "@/components/diffEditor.vue";

// import { useStore } from 'vuex';
// let { proxy } = getCurrentInstance();
// const store = useStore()
// const route = useRoute()
import { diffChars } from "diff";
import { html as diff2html } from "diff2html";
import "diff2html/bundles/css/diff2html.min.css";

onMounted(() => {
  setTimeout(() => {
    initEditor();
  }, 70);
  const jsMark = new JsMark({
    el: document.querySelector(".c-js-mark"),
    options: {
      isCover: true,
    },
  });
  jsMark.onClick = function (res) {
    // 点击已经标注的内容后，会触发jsMark.onClick方法,回掉方法接受一个uid为标签上唯一的一个id，可用于清除单个标注
    // document
    //   .querySelectorAll('[data-selector="' + res.uid + '"]')
    //   .forEach((item) => {
    //     item.classList.remove("c-danger");
    //   });
    // jsMark.clearMark(uid);
    // 清除标签上data-selector属性为唯一uid的标签标注  jsMark.clearMarkAll();清除所有标注
  };
  jsMark.onSelected = function (res) {
    // textNodes: Text[]; //选中的所有文本节点,onSelected返回值的res.textNodes
    // className: string; //需要标注的文本节点样式类
    // uuid?: string; //标注文本节点的唯一id，会绑定到节点身上的data-selector属性，此id可用于清除当前标注节点，可选，不传会自动生成
    // storeRenderOther?:any; //来自jsMark.renderStore方法的用户自定义参数

    jsMark.repaintRange({
      textNodes: res.textNodes,
      className: value5.value ? "c-success" : "c-danger",
    });
  };
});
const a = ref("这是第一1123454行文字。\n这是第二行文字。1");
const a1 = ref("这是第一行文字。\n\n\n这是2235第二行文字。1");

const className = ref("c-danger");
const value5 = ref(false);
const diffString = diffChars(a.value, a1.value);
const html = ref("");
const html1 = ref("");
diffString.forEach((item) => {
  let itemhtml = item.value;
  if (item.added) {
    html1.value += '<span class="added">' + item.value + "</span>";
  } else if (item.removed) {
    html.value += '<span class="removed">' + item.value + "</span>";
  } else {
    html.value += itemhtml;
    html1.value += itemhtml;
  }
});

let arr = html.value.split("\n");
let arr1 = html1.value.split("\n");
let rowhtml = "";
let rowhtml1 = "";
arr.forEach((item, index) => {
  rowhtml += '<div class="row">' + item + "</div>";
});
arr1.forEach((item, index) => {
  rowhtml1 += '<div class="row">' + item + "</div>";
});
html.value = rowhtml;
html1.value = rowhtml1;

setTimeout(() => {
  document.querySelectorAll(".diff .row").forEach((item) => {
    if (item.querySelector(".added")) {
      item.classList.add("on");
    }
    if (item.querySelector(".removed")) {
      item.classList.add("off");
    }
  });
}, 100);
// const diffHtmlReport = diff2html.getPrettyHtml(diffString, { inputFormat: 'diff' });

const initDiffHtml = () => {
  // html.value = diffHtmlReport
};
initDiffHtml();

const doc = ref("<div> 这个标 <span></span>签的含义是啥");

const isShowdiffEditor = ref(false);

const editorContainer = ref(null);
let editorInstance = null;

let originalModel;
let modifiedModel;
let monacoDiffInstance;
// https://aydk.site/editor/interfaces/IDiffEditorBaseOptions.html#experimental
let defopt = {
  value: "111",
  theme: "IDLE", // 编辑器主题：vs, hc-black, or vs-dark，更多选择详见官网
  roundedSelection: false, // 右侧不显示编辑器预览框
  autoIndent: true, // 自动缩进
  readOnly: false, // 是否只读
  diffWordWrap: "on",  //描述：是否在差异编辑器中启用单词换行可选项： "on" | "off" | "inherit"
  ignoreTrimWhitespace:true,  //描述：是否忽略差异编辑器中的空格。
  wordWrap: "on",
  automaticLayout: true,
  scrollBeyondLastLine: false,
  scrollbar: {
    verticalScrollbarSize: 0,
  },
  contextmenu: false,
  fontSize: props.fontSize || 14,
    fontFamily:
      "'Helvetica Neue', Helvetica, Tahoma, Arial, 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', 'Heiti SC', 'WenQuanYi Micro Hei', sans-serif !important",
    lineNumbers: props.lineNumbers || "off",
    hover: false,
    minimap: {
      enabled: false, // 设置minimap不可用
    },
};

const initEditor = () => {
  editorInstance = monaco.editor.createDiffEditor(
    editorContainer.value,
    defopt
  );
  originalModel = monaco.editor.createModel(
    "function add(a, b) { return a + b; }",
    "text/javascript"
  );
  modifiedModel = monaco.editor.createModel(
    "function add(a, b) { return a + b; }",
    "text/javascript"
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
  <el-button @click="isShowdiffEditor = true">对比文本</el-button>
  <div style="width: 100%; height: calc(100% - 500px)">
    <div class="editor-containbox nodrag nowheel">
      <div
        ref="editorContainer"
        class="editor-container c-scroll-contain"
      ></div>
    </div>
  </div>
  <div style="width: 50%; height: calc(100% - 500px)" id="container1"></div>
  <div style="width: 50%; height: calc(100% - 500px)" id="container2"></div>

  <div class="c-js-mark"></div>

  <diffEditor :newval="a" :oldval="a1" v-model="isShowdiffEditor"></diffEditor>
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
