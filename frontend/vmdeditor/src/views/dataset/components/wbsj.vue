<script setup>
import { ref, nextTick, onMounted, onUnmounted, reactive, watch,computed  } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter, onBeforeRouteUpdate } from "vue-router";
import { Search, UploadFilled } from "@element-plus/icons-vue";
import icon from "@/components/icon.vue"
import {
  documentsGet,
  documentsEdit,
  documentsEditMd,
  documentsHistory,
  documentsHistoryDetail,
  documentsAddMarkDown,
  upload,
  documentsMarkdown,
  model_configall
} from "@/api/api";

import CompApp from "@/views/app/list.vue";

const props = defineProps({
  id: {
    type: [String, Number],
    default: () => 0,
  },
});

const route = useRoute();
const router = useRouter();
const store = useStore();

// const onbeforefn = (e) => {
//   var e = window.event||e;
//    　　e.returnValue=("系统可能不会保存您所做的更改。");
// }

const isConfirm = ref(true);

// onBeforeRouteUpdate((to, from,next) => {
//   if(!isConfirm.value){
//     next();
//     return ;
//   }
//   _this.$confirm("系统可能不会保存您所做的更改。").then((res) => {
//     next();
//   }).catch((err) => {
//     next(false);
//   })
// })

onMounted(async () => {
  // window.addEventListener("beforeunload", onbeforefn)
});

// onUnmounted(() => {
//   window.removeEventListener("beforeunload", onbeforefn)
// })

const did = ref(route.query.did);

const curstep = ref(1);

const fileList = ref([]);
const handleChange = (uploadFile, uploadFiles) => {
  fileList.value = uploadFiles;
};
const curDomDetail = ref(null);

const mkData = ref("");
const is_markdown = ref(false);

const domname = ref("");
const domname_clone = ref("");

const changePage = (id) => {
  let query = { ...route.query };
  query.it = 2;
  query.did = id;
  router.replace({ path: route.path, query: query });
};
const mkData_clone = ref("");
const getDomDetail = (fn) => {
  documentsGet({ id: did.value }).then((res) => {
    curDomDetail.value = res;
    domname.value = res.name;
    domname_clone.value = res.name;
    if (res.is_markdown) {
      mkData.value = res.markdown_content;
      mkData_clone.value = res.markdown_content;
    } else {
      mkData.value = res.content;
      mkData_clone.value = res.content;
    }

    is_markdown.value = res.is_markdown;
    fn && fn();
  });
};

if (route.query.it == 2) {
  getDomDetail();
}

const beforeAvatarUpload = (file) => {
  store.commit("loading", true);
  if (/\.(xlsx|xls|xlsm|txt)$/i.test(file.name)) {
  }

  return true;
};

// 进度条
const customColorMethod = (percentage) => {
  if (percentage < 30) {
    return "#909399";
  }
  if (percentage < 70) {
    return "#e6a23c";
  }
  return "#67c23a";
};

const goback = () => {
  let query = { ...route.query };
  query.it = 0;
  router.replace({ path: route.path, query: query });
};

let url = "/api/documents/add?knowledgebase_id=" + route.query.id;
if (route.query.category_id) {
  url += "&category_id=" + route.query.category_id;
}
const actionurl = ref(url);

const sucfn = (res, file, files) => {
  store.commit("loading", false);
  console.log(res, file, files);
};
const errfn = (err) => {
  store.commit("loading", false);
  let myError = err.toString();
  myError = myError.replace("UploadAjaxError: ", "");
  myError = JSON.parse(myError);
  _this.$message(myError.detail, "error");
};

const subfn = (val, isIndex) => {
  isConfirm.value = false;
  if (domname.value.length == 0 || mkData.value.length == 0) {
    _this.$message("文档名称、内容不可为空", "error");
    return false;
  }
  // if(domname.value === domname_clone.value && mkData.value === mkData_clone.value) {
  //   _this.$message("文档名称、内容没有变化，无需保存", "error");
  //   return false
  // };
  documentsEdit({
    id: did.value,
    text: mkData.value,
    name: domname.value,
    is_markdown: is_markdown.value,
  }, isIndex).then((res) => {
    _this.$message("保存成功");
    goback();
  });
};

const curver = ref(0);

const getDetail = (item) => {
  curver.value = item.ver;
  documentsHistoryDetail({ ver: item.ver, id: did.value }).then((res) => {
    mkData.value = res.content;
    is_markdown.value = res.is_markdown;
  });
};

// 链接上传
const form = reactive({ text: "", name: "", region: "", llm_type: 1 });
const form1 = reactive({ link: "", name: "" });
const zlform = reactive({ text: "", name: "", checkList: [], llm_type: 1 });

const isZlDialog = ref(false);

const addMd = async () => {
  let prompt_id = null;
  if (zlform.checkList.length > 0) {
    prompt_id = zlform.checkList[0].id;
  }
  documentsMarkdown({
    id: did.value,
    llm_id: zlform.llm_type,
    prompt_id,
    content: mkData.value,
  })
    .then((res) => {
      if (res.result == 'success') {
        isZlDialog.value = false;
        _this.$message("整理成功");
        mkData.value = res.content;
      }

    })
};

const mdloading = ref(false);

const promptsList = ref([]);

const checkList = ref([]);
const drawer = ref(false);

const createMd = () => {
  if (form.name.length == 0 || form.text.length == 0) {
    _this.$message("文档名称、内容不可为空", "error");
    return false;
  }
  if (mdloading.value) return false;
  mdloading.value = true;

  documentsAddMarkDown({
    knowledgebase_id: parseInt(route.query.id),
    category_id: parseInt(route.query.category_id) || 0,
    name: form.name,
    content: form.text,
  })
    .then((res) => {
      did.value = res.id;
      changePage(res.id);
      getDomDetail();
    })
    .finally(() => {
      mdloading.value = false;
    });
};

const isMdShow = ref(false);

const historylist = ref([]);
if (route.query.it == 2) {
  documentsHistory({ id: did.value }).then((res) => {
    historylist.value = res || [];
  });
}

import { getTime } from "@/components/comp.js";

const changeMDType = (flag) => {
  is_markdown.value = flag;
  if (!flag) {
    mkData.value = curDomDetail.value.content;
  } else {
    mkData.value = curDomDetail.value.markdown_content;
  }
};

const llmlist = ref([]);
//  获取大模型配置
model_configall({ page: 1, pagesize: 10000 }).then((res) => {
  llmlist.value = res || [];
});

const handleUploadImage = (event, insertImage, files) => {
  // 拿到 files 之后上传到文件服务器，然后向编辑框中插入对应的内容
  upload({ file: files[0] })
    .then((res) => {
      // 此处只做示例
      insertImage({
        url: res.file_path,
        desc: "",
        // width: 'auto',
        // height: 'auto',
      });
    })
    .catch((err) => { });
};

const shouldShowFooter = computed(() => {
  const isCase1 = route.query.it == 2 || isMdShow.value;
  const isCase2 = route.query.it == 1 && !isMdShow.value && curstep.value == 2;
  return isCase1 || isCase2;
})
</script>
<template>
  <div class="page-wbsj">
    <div class="mg20">
      <div class="tl backbox">

        <div v-if="route.query.it == 1 && !isMdShow" class="groupbtns">
          <el-button plain :style="curstep == 1 ? 'background:none;' : 'background:#fff;'"
            @click="curstep = 2">手工录入</el-button>

          <el-button plain :style="curstep == 2 ? 'background:none;' : 'background:#fff;'"
            @click="curstep = 1">上传文档</el-button>
        </div>
        <div v-if="route.query.it == 2" class="groupbtns">
          <el-button type="primary" :style="is_markdown ? 'background:none;' : 'background:#fff;'" plain
            @click="changeMDType(!is_markdown)">编辑源文档</el-button>
          <el-button :style="!is_markdown ? 'background:none;' : 'background:#fff;'" plain
            @click="changeMDType(!is_markdown)">编辑markdown文档</el-button>
        </div>

        <span style="float: right;"  @click="goback()" class="c-iconbackbox">
          <span class="iconfont icon-fuwenben-chexiao"></span> 返回
        </span>
      </div>

      <template v-if="route.query.it == 2 || isMdShow">
        <div style="margin-top: 20px;" class="mdbox">
          <div v-if="route.query.it == 2" class="historybox c-history">
            <div class="title">历史记录</div>
            <el-scrollbar style="height: calc(100% - 40px);">
              <div class="empty" v-if="historylist.length < 1">暂无历史数据</div>
              <div v-for="item in historylist" @click="getDetail(item)" :key="item.ver"
                :class="{ on: item.ver == curver }" class="item">
                <div :title="item.name" class="name ellipsis3">
                  {{ item.name }}<span style="margin-left: 5px;" class="c-warn-btn c-mini radius">{{ item.ver }}</span> 
                </div>
                <div class="timebox">
                  <span class="time">{{ getTime(item.created_at) }}</span>
                </div>
              </div>
            </el-scrollbar>
          </div>
          <div class="mdeditor">
            <div v-if="route.query.it == 2" class="namebox re">
              <span class="display:inline-block;width:86px;">文件名称：</span>
              <el-input style="width: calc(100% - 86px);" v-model="domname" type="text"></el-input>
              <el-button style="position: absolute;top:0;right:0;border-radius:6px;" @click="isZlDialog = true;"
                type="primary">AI整理</el-button>
            </div>
            <div class="mdcontain">
              <v-md-editor :disabled-menus="[]" @upload-image="handleUploadImage" @save="subfn(mkData)" v-model="mkData"
                height="100%"></v-md-editor>
            </div>
          </div>
        </div>

      </template>
      <template v-else-if="route.query.it == 1">
        <div v-show="curstep == 1" class="uploadbox">
          <el-upload class="upload-demo" v-model:file-list="fileList"
            :headers="{ authorization: 'Bearer ' + store.state.token }" :before-upload="beforeAvatarUpload"
            :on-change="handleChange" :show-file-list="false" :on-error="errfn" :on-success="sucfn" drag
            :action="actionurl" multiple>
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              点击或拖动文件到此处上传 <br />
              <div class="tip">
                支持 .txt, .docx, .csv, .xlsx, .pdf, .md类型文件
                <br />最多支持 15 个文件。单个文件最大 100 MB。
              </div>
            </div>
          </el-upload>
        </div>
        <div v-show="curstep == 1 && fileList.length > 0" class="tablebox c-tablebox">
          <el-table :data="fileList" :max-height="store.getters.innerHeight - 500" style="width: 100%">
            <el-table-column label="文件名">
              <template #default="scope">
                <div style="display: flex; align-items: center">
                  <span style="margin-left: 10px">{{ scope.row.name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="进度条">
              <template #default="scope">
                <el-progress :percentage="scope.row.status == 'success'
                  ? scope.row.percentage
                  : Math.min(scope.row.percentage, 98)
                  " striped :color="customColorMethod" />
              </template>
            </el-table-column>
            <el-table-column label="文件大小">
              <template #default="scope">
                <div style="display: flex; align-items: center">
                  <span style="margin-left: 10px">{{ scope.row.size }}</span>
                </div>
              </template>
            </el-table-column>

            <template #empty="scope">
              <div class="c-emptybox">
                <icon type="empzwssjg" width="100" height="100"></icon>暂无数据~~
              </div>
            </template>
          </el-table>
        </div>
        <div style="padding: 20px 0 0 0;" v-show="curstep == 2">
          <el-form class="tl" :model="form" label-width="auto" label-position="top"
            :style="historylist.length > 0 ? 'max-width: 800px' : '100%'">

            <el-form-item label="文档名称">
              <el-input maxlength="100" v-model="form.name" />
            </el-form-item>
            <el-form-item label="文档内容">
              <el-input v-model="form.text" :rows="26" type="textarea" placeholder="" />
            </el-form-item>
          </el-form>

        </div>
      </template>
    </div>

    <el-dialog align-center v-model="isZlDialog" title="整理文档" width="900">
      
        <el-form class="tl" :model="zlform" label-width="auto" label-position="top" style="width: 100%;">
          <el-form-item label="大模型类型">
            <el-select v-model="zlform.llm_type" filterable :reserve-keyword="false" placeholder="">
              <el-option v-for="item in llmlist" :value="parseInt(item.id, 10)" :label="item.name"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="提示词">


            <div @click="drawer = true" class="c-switchbox pointer">
              <span v-if="zlform.checkList.length > 0">{{
                zlform.checkList[0].name
                }}</span>
              <span class="placeholder" v-else>请选择提示词</span>
              <span style="position: absolute;top: -36px;right: 0;color:var(--el-color-primary)"
                class="c-pointer">选择</span>
            </div>
          </el-form-item>
        </el-form>
        <template #footer>
        <div class="dialog-footer">
          <el-button @click="isZlDialog = false">取消</el-button>
          <el-button type="primary" @click="addMd()"> 确定提交 </el-button>
        </div>
      </template>
    </el-dialog>
    <el-drawer v-model="drawer" size="90%" title="" direction="rtl">
      <CompApp @subfn="
        (itemlist) => {
          drawer = false;
          zlform.checkList = itemlist;
        }
      " :isCheck="true" :checkList="zlform.checkList"></CompApp>
    </el-drawer>

    <div v-if="shouldShowFooter" class="c-footerbtns" style="bottom: -20px;justify-content: flex-end;">

      <template v-if="route.query.it == 2 || isMdShow">
        <el-button v-if="is_markdown" @click="subfn(mkData, true)" type="primary">保存并同步向量库</el-button>
        <el-button @click="subfn(mkData)" plain>保存</el-button>
        
      </template>
      <template v-if="route.query.it == 1 && !isMdShow && curstep == 2">
        <el-button @click="createMd()" :loading="mdloading" type="primary">保存</el-button>
       
      </template>
     

      
    </div>
  </div>
</template>
<style scoped>
.mg20 {
  margin: 0 20px;
  height: 100%;
}

.groupbtns {
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  background: #F1F3F4;
  padding: 4px;
  border-radius: 25px;
}

.namebox {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  font-size: 16px;
  margin-bottom: 10px;
}

.mdbox {
  height: calc(100% - 54px);
  text-align: left;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  width: 100%;
  position: relative;
}

.historybox .title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
}

.mdbox .historybox {
  width: 200px;
  height: 100%;
  flex-shrink: 0;
  box-sizing: border-box;
  padding-right: 10px;
  position: relative;
}

.historybox .timebox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #aaa;
}

.historybox .name {
  font-weight: bold;
  font-size: 16px;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  line-height: 20px;
}


.mdbox .mdeditor {
  width: calc(100% - 200px);
  height: 100%;
  overflow: hidden;
}

.mdcontain {
  height: calc(100% - 40px);
}

.btns {
  text-align: center;
  padding-top: 20px;
}

.page-wbsj {
  display: block;
  position: relative;
  margin: 0 -20px;
  height: calc(100% - 60px);
  padding-bottom: 60px;
}

.backbox {
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.icon-fanhui {
  font-size: 26px;
  margin-right: 5px;
}

.stepbox {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--chakra-colors-myGray-50);
  border-radius: var(--chakra-radii-md);
  border: 1px solid var(--chakra-colors-borderColor-low);
  padding: 10px;
  margin-top: 10px;
}

.uploadbox {
  margin: 20px 0;
}

.step2 {
  position: relative;
  display: flex;
  width: 100%;
  height: calc(100% - 120px);
}

.step2 .lbox {
  flex-shrink: 0;
  margin-right: 20px;
  width: 540px;
}

.step2 .rbox {
  width: calc(100% - 520px);
}

.step2 .title {
  text-align: left;
  font-size: 16px;
  padding: 16px 0;
}

.step2 .radbox {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-bottom: 20px;
}

.step2 .radbox .label {
  width: 100px;
  flex-shrink: 0;
  font-size: 14px;
  text-align: left;
}

.step2 .title .icon-font {
  font-size: 20px;
}

.step2 .radbox .h60 {
  height: 60px;
  margin-bottom: 10px;
}

.step2 .radbox .ritem {
  width: 384px;
  text-align: left;
}

.step2 .radbox .ritem .text {
  font-size: 16px;
  font-weight: bold;
}

.step2 .radbox .ritem .intro {
  font-size: 12px;
}

.sourcelist {
  height: calc(100% - 50px);
  overflow-y: auto;
}

.sourcelist .item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--chakra-space-4);
  border-radius: var(--chakra-radii-md);
  box-shadow: var(--chakra-shadows-2);
  border: 1px solid var(--chakra-colors-borderColor-low);
  margin-bottom: 10px;
  width: 100%;
  box-sizing: border-box;
}
</style>