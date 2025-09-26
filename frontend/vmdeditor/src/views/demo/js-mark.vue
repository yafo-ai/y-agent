<script setup>
// import { useRoute } from 'vue-router'
import { ref, onMounted, onBeforeUnmount, reactive, watch } from "vue";
import JsMark from "js-mark";
import VueDiff from "vue-diff";
import "vue-diff/dist/index.css"
// import { useStore } from 'vuex';
// let { proxy } = getCurrentInstance();
// const store = useStore()
// const route = useRoute()
import { diffChars } from 'diff';
import { html as diff2html } from 'diff2html';
import 'diff2html/bundles/css/diff2html.min.css';
const isConsole = ref(window.localStorage.getItem('vConsole'))
const change = () =>{
  isConsole.value = !isConsole.value;
  if(isConsole.value){
    // 开启调试模式
    window.localStorage.setItem('vConsole',true);
  }else{
    window.localStorage.removeItem('vConsole');
  }
  window.location.reload();
}
const container = ref()
onMounted(() => {
  const jsMark = new JsMark({
    el:document.querySelector(".c-js-mark"),
    options:{
        isCover:true
    }
  })
  jsMark.onClick = function (res) {
    // 点击已经标注的内容后，会触发jsMark.onClick方法,回掉方法接受一个uid为标签上唯一的一个id，可用于清除单个标注
    document.querySelectorAll('[data-selector="'+res.uid+'"]').forEach((item)=>{
      item.classList.remove('c-danger')
    })
    // jsMark.clearMark(uid);
    // 清除标签上data-selector属性为唯一uid的标签标注  jsMark.clearMarkAll();清除所有标注
  };
  jsMark.onSelected = function (res) {
    // textNodes: Text[]; //选中的所有文本节点,onSelected返回值的res.textNodes
    // className: string; //需要标注的文本节点样式类
    // uuid?: string; //标注文本节点的唯一id，会绑定到节点身上的data-selector属性，此id可用于清除当前标注节点，可选，不传会自动生成
    // storeRenderOther?:any; //来自jsMark.renderStore方法的用户自定义参数

    jsMark.repaintRange({
        textNodes:res.textNodes,
        className:value5.value?'c-success':'c-danger',
    });
  };
});

const value5 = ref(false)
// const diffHtmlReport = diff2html.getPrettyHtml(diffString, { inputFormat: 'diff' });
const html = ref('')
const initDiffHtml = () => {
  // html.value = diffHtmlReport
}
initDiffHtml()
</script>

<template>
  <el-switch
    v-model="value5"
    class="ml-2"
    inline-prompt
    style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
    active-text="错误"
    inactive-text="优秀"
  />
  <br>

  <div class="c-js-mark" ref="container">

    1
    3455
    <br>
    1
    3455
    <br> 1
    3455
    <br> 1
    3455
    <br> 1
    3455
    <br> 1
    3455
    <br> 1
    3455
    <br> 1
    3455
    <br> 1
    3455
    <br> 1
    3455
    <br>
  </div>
  <div v-html="html">
 
  </div>
</template>

<style scoped>

</style>
