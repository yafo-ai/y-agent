<script setup>
import { ref, nextTick, onMounted, reactive, watch } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";

const props = defineProps({
  curContext: {
    type: Array,
    default: [],
  },
  type: {
    type: String,
    default: "text",
  },
  title: {
    type: String,
    default: "引用内容",
  },
  modelValue: { type: Boolean, default: false },
});
const emits = defineEmits(["subfn", "update:modelValue"]);
const route = useRoute();
const router = useRouter();
const store = useStore();

const dialogFormVisible = ref(false);
const scrollbarRef = ref(null);
const scrollbarRef1 = ref(null);
const size = ref('1000px');
watch(
  () => props.modelValue,
  (n) => {
    dialogFormVisible.value = n;
    if (n) {
      if (props.type == 'img') {
        mkDataIndex.value = -1;
        size.value = '800px';
      } else {
        mkDataIndex.value = 0;
        size.value = '1200px';
      }
      setTimeout(() => {
        let arr = document.querySelectorAll(".js-intro");
        arr.forEach((item, index) => {
          if (item.offsetHeight < item.querySelector(".text").offsetHeight) {
            item.querySelector(".js-btn").style.cssText = "";
          }
        });
      }, 300);
    }
  }
);

const close = () => {
  emits("update:modelValue", false);
};

const sub = (params) => {
  emits("subfn", params);
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
  return 'c-topicon'+curtype;
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

const open = (item) => {
  item.isOpen = true;

};
const mkDataIndex = ref(0);
</script>
<template>
  <el-drawer :title="title" @closed="close" v-model="dialogFormVisible" direction="rtl" :size="size">
    <div class="drawerbox">
      <div class="dtop">
        <div class="contextbox">
          <el-scrollbar ref="scrollbarRef">
            <div class="mg20">
            <template v-if="type == 'img'">
              <!-- 图片引用 -->
              <div class="item" v-for="item in curContext">
                <img class="cimg" :src="item.link" :key="item.link" :title="item.desc" :alt="item.desc" />
              </div>
            </template>
            <template v-else>
              <div v-for="(item, index) in curContext" @click="mkDataIndex = index" :key="item.metadata.knowledgebase_id +
                '_' +
                item.ref_real_id +
                '_' +
                item.ref_id +
                '_' +
                item.metadata.id
                " class="item" :class="{ on: index == mkDataIndex }">
                <div class="title">
                  <span :class="getIcon(item.metadata.type)"></span>
                  <div class="filename ellipsis">
                    {{ item.metadata.filename }}
                  </div>
                  
                </div>
                <div :title="item.page_content" class="intro js-intro" :class="{ open: item.isOpen }">
                  <div v-html="item.page_content.replace(/\n/g, '<br>')" class="text"></div>
                  <span v-if="!item.isOpen" @click="item.isOpen=true; " style="display: none" class="js-btn">展开</span>
                </div>
                <div class="score tl">
                  <div class="c-scorebox">
                    {{ item.metadata.score || 0 }}
                  </div>
                  <el-button size="small" v-if="$route.path != '/sharechat'" @click.stop="goDetail(item)"
                    type="primary">查看文档</el-button>
                </div>
              </div>
            </template>
          </div>
          </el-scrollbar>
        </div>
        <div class="editorbox">
          <el-scrollbar ref="scrollbarRef1">
            <div class="mg20">
            <v-md-preview v-if="mkDataIndex >= 0" :text="curContext[mkDataIndex].page_content"></v-md-preview>
          </div>
          </el-scrollbar>
        </div>
      </div>

    </div>
  </el-drawer>
</template>
<style scoped>
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

.editorbox {
  text-align: left;
  width: 50%;
  height: 100%;
}

.contextbox {
  width: 50%;
  height: 100%;
  background: var(--c-lbg-color);
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

.contextbox .item .title .filename{
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
.drawerbox .mg20{
  margin: 20px;
}
.drawerbox :deep(.github-markdown-body){
  padding: 0;
}
</style>