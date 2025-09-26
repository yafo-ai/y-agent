<script setup>
import { ref, nextTick, onMounted, reactive, watch } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";

import { knowledges, similaritysearch } from "@/api/api";
import icon from "@/components/icon.vue"
const props = defineProps({
  xlform: {
    type: Object,
    default: {
      knowledgebase_k: 5,
      knowledgebase_ids: [],
      file_knowledgebase_ids: [],
      product_model_ids: [],
      file_knowledgebase_k: 5,
      product_model_top_k: 5,
      question: "",
    },
  },
  type: {
    type: String,
    default: "text",
  },
  title: {
    type: String,
    default: "向量检测",
  },
  modelValue: { type: Boolean, default: false },
});
const emits = defineEmits(["subfn", "update:modelValue"]);
const route = useRoute();
const router = useRouter();
const store = useStore();


watch(
  () => props.modelValue,
  (n, o) => {
    xlDialog.value = n;
    if (n && n !== o) {
      // init
      init()
    }
  }
);
const textlist = ref([]);
const splist = ref([]);
const excellist = ref([]);

const init = () => {
  xlform.value = props.xlform;
  curContext.value = [];
  if (textlist.value.length > 0 && splist.value.length > 0 && excellist.value.length > 0) {
    // 如果已经获取过  不重复获取
    return false;
  }
  knowledges().then((res) => {
    let arr = res || [];
    textlist.value = [];
    splist.value = [];
    excellist.value = [];
    arr.forEach((item) => {

      if (item.type == 2) {
        splist.value.push(item);
      } else if (item.type == 1) {
        textlist.value.push(item);
      } else if (item.type == 3) {
        excellist.value.push(item);
      }
    });
  });
};

const close = () => {
  emits("update:modelValue", false);
};

const sub = (params) => {
  emits("subfn", params);
};

const xlform = ref({
  knowledgebase_k: 5,
  knowledgebase_ids: [],
  file_knowledgebase_ids: [],
  product_model_ids: [],
  file_knowledgebase_k: 5,
  product_model_top_k: 5,
  question: "",
});

const similaritysearchfn = () => {
  if (!xlform.value.question) {
    return false;
  }
  similaritysearch(xlform.value).then((res) => {
    res.forEach((citem) => {
      citem.isOpen = false;
    });
    curContext.value = res;
    nextTick(() => {
      let arr = document.querySelectorAll(".js-intro");
      arr.forEach((item, index) => {
        if (item.offsetHeight < item.querySelector(".text").offsetHeight) {
          item.querySelector(".js-btn").style.cssText = "";
        }
      });
    });
  });
};
const getIcon = (type) => {
  // 定义一个对象来映射type到curtype的值，使得代码更简洁且易于维护
  const typeToCurtypeMap = {
    "knowledge_document": 1,
    "product_model": 2,
    "excel_document": 3
  };

  // 使用逻辑或操作符为curtype提供一个默认值
  const curtype = typeToCurtypeMap[type] || 1;
  return 'c-topicon' + curtype;
};
const goDetail = (item) => {

  if (item.metadata.detali_url) {
    window.open(item.metadata.detali_url);
  } else {
    let id = item.metadata.knowledgebase_id;
    let type = item.metadata.type;
    let did = item.metadata.ref_real_id;
    let rid = item.metadata.ref_id;
    window.open(`/chat/detail?id=${id}&type=${type}&did=${did}&rid=${rid}`);
  }
};
const curContext = ref([]);
const xlDialog = ref(false);
const mkDataIndex = ref(0);
</script>
<template>
  <el-drawer v-model="xlDialog" title="向量检测" @closed="close" direction="rtl" size="800px">
    <div class="xlcontent">
      <el-scrollbar>
        <div class="mg20">
          <el-form class="tl" inline :model="xlform" label-width="auto" label-position="top">
            <el-form-item style="width: calc(100% - 236px);margin-right: 16px;" label="文本知识库">
              <el-select v-model="xlform.knowledgebase_ids" multiple collapse-tags :max-collapse-tags="2" placeholder="请选择文本知识库">
                <el-option v-for="item in textlist" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </el-form-item>
            <el-form-item style="width: 220px;margin-right: 0;" label="top_k">
              <el-input-number style="width: 100%" placeholder="请填写文本top_k" v-model="xlform.knowledgebase_k" :min="0"
                :max="1000" :precision="0" :step="1" controls-position="right" />
            </el-form-item>
            <!-- <el-form-item style="width: calc(100% - 236px);margin-right: 16px;" label="商品知识库">
              <el-select v-model="xlform.product_model_ids" multiple collapse-tags :max-collapse-tags="2" placeholder="请选择商品知识库">
                <el-option v-for="item in splist" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </el-form-item>
            <el-form-item style="width: 220px;margin-right: 0;" label="商品top_k">
              <el-input-number style="width: 100%" v-model="xlform.product_model_top_k" placeholder="请填写商品top_k"
                :min="0" :max="1000" :precision="0" :step="1" controls-position="right" />
            </el-form-item> -->
            <el-form-item style="width: calc(100% - 236px);margin-right: 16px;" label="EXCEL参数库">
              <el-select v-model="xlform.file_knowledgebase_ids" multiple collapse-tags :max-collapse-tags="2" placeholder="请选择EXCEL参数库">
                <el-option v-for="item in excellist" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </el-form-item>
            <el-form-item style="width: 220px;margin-right: 0;" label="EXCEL参数库top_k">
              <el-input-number style="width: 100%" placeholder="请填写EXCEL参数库top_k" v-model="xlform.file_knowledgebase_k"
                :min="0" :max="1000" :precision="0" :step="1" controls-position="right" />
            </el-form-item>
            <el-form-item style="width: 100%;margin-right: 0px;" label="检测内容">
              <el-input v-model="xlform.question" style="width: 100%" class="autofocus" type="text"
                placeholder="请填写检测内容" />
              <el-button @click="similaritysearchfn()"
                style="position: absolute;right: 0;top: 0;border-radius: var(--el-border-radius-base);"
                type="primary">检测</el-button>
            </el-form-item>
          </el-form>

          <div class="contextbox">
            <div class="xltitle">检测结果 <span class="c-primary-btn c-mini">{{ curContext.length }}</span> </div>
            <div style="padding-bottom: 24px;" v-if="curContext.length < 1" class="c-emptybox">
              <icon type="empzwssjg" width="100" height="100"></icon>暂无检测结果
            </div>
            <div v-for="(item, index) in curContext" :key="item.metadata.knowledgebase_id +
              '_' +
              item.ref_real_id +
              '_' +
              item.ref_id +
              '_' +
              item.metadata.id
              " class="item">
              <div class="title">
                <span :class="getIcon(item.metadata.type)"></span>
                <div class="filename ellipsis">
                  {{ item.metadata.filename }}
                </div>

              </div>
              <div :title="item.page_content" class="intro js-intro" :class="{ open: item.isOpen }">
                <div v-html="item.page_content.replace(/\n/g, '<br>')" class="text"></div>
                <span v-if="!item.isOpen" @click="item.isOpen = true;" style="display: none" class="js-btn">展开</span>
              </div>
              <div class="score tl">
                <div class="c-scorebox">
                  {{ item.metadata.score || 0 }}
                </div>
                <el-button size="small" v-if="$route.path != '/sharechat'" @click.stop="goDetail(item)"
                  type="primary">查看文档</el-button>
              </div>
            </div>
          </div>
        </div>
      </el-scrollbar>
    </div>
    <br />

  </el-drawer>
</template>
<style scoped>
.mg20 {
  margin: 20px;
}


.score {
  color: #aaa;
  margin-top: 5px;
}

.contextbox .item {
  box-sizing: border-box;
  padding: 20px;
  border: 1px solid var(--el-border-color);
  border-radius: 5px;
  margin-bottom: 20px;
  text-align: left;
  position: relative;
}

.contextbox .item .title {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.xlcontent {
  margin: -20px;
  height: calc(100% - -20px);
}

.xltitle {
  text-align: left;
  padding: 20px 0px;
  font-size: 14px;
}

.footer {
  clear: both;
  text-align: center;
}

.js-btn {
  cursor: pointer;
  position: absolute;
  right: 20px;
  bottom: 64px;
  background: #fff;
  padding: 4px;
  color: var(--el-color-primary);
  display: inline-block;
  font-size: 12px;
}

.score {
  margin-top: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.intro {
  display: block;
  height: 60px;
  overflow: hidden;
  line-height: 20px;
}

.intro.open {
  height: auto;
}

.rutilbox .iconfont {
  cursor: pointer;
  margin-left: 5px;
}

.rutilbox .iconfont:hover {
  color: var(--el-color-primary);
}

.rutilbox .iconfont.on {
  transform: rotate(180deg);
  display: inline-block;
}

.icon-zhishiku {
  color: var(--el-color-primary);
}

.icon-zhishikuguanli {
  color: var(--el-color-success);
}

.dtop {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  width: 100%;
  height: calc(100% - 0px);
}


.contextbox {
  height: 100%;
  background: var(--c-lbg-color);
  box-sizing: border-box;
  margin: 0 -20px;
  padding: 0 20px;
  border-top: 1px solid var(--el-border-color);
}

.contextbox .item {
  box-sizing: border-box;
  padding: 20px;
  border: 1px solid #fff;
  border-radius: 16px;
  margin-bottom: 20px;
  text-align: left;
  position: relative;
  transition: all 0.2s;
  background: #fff;
  cursor: pointer;
}

.contextbox .item.on {
  border-color: var(--el-color-primary);
}

.contextbox .item .title {
  display: flex;
  align-items: center;
  justify-content: flex-start;

}

.contextbox .item .title .filename {
  padding-left: 20px;
  font-weight: bold;
  font-size: 20px;
  color: #333;
  max-width: calc(100% - 60px);
}

.utils {
  font-size: 12px;
  padding-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid #ddd;
  margin-top: 10px;
}

.drawerbox {
  display: block;
  height: calc(100% + 40px);
  margin: -20px;
}

.drawerbox .mg20 {
  margin: 20px;
}

.drawerbox :deep(.github-markdown-body) {
  padding: 0;
}
</style>