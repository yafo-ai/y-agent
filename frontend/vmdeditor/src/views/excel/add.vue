<script setup>
import { ref, nextTick, onMounted, onUnmounted, reactive, watch } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter, onBeforeRouteUpdate } from "vue-router";

import { Search, UploadFilled } from "@element-plus/icons-vue";
import { goback } from "@/components/comp.js";
import icon from "@/components/icon.vue"


const route = useRoute();
const router = useRouter();
const store = useStore();



const fileList = ref([]);
const handleChange = (uploadFile, uploadFiles) => {
  fileList.value = uploadFiles;
};



const beforeAvatarUpload = (file) => {
  if (/\.(xlsx)$/i.test(file.name)) {
  } else {
    _this.$message("上传的文件格式不正确", "error");
    return false;
  }
  store.commit("loading", true);
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

const curtype = ref("1001");
const options = ref({
  1001: "产品参数模板",
});

let actionurl = ref("/api/filedatabase/add?template_type=" + curtype.value + "&knowledgebase_id=" + route.query.id);
const typechange = (val) => {
  actionurl.value = "/api/filedatabase/add?template_type=" + val + "&knowledgebase_id=" + route.query.id;
}



const sucfn = (res, file, files) => {
  store.commit("loading", false);
  fileList.value = [];
};
const errfn = (err) => {
  store.commit("loading", false);
  let myError = err.toString();
  myError = myError.replace("UploadAjaxError: ", "");
  myError = JSON.parse(myError);
  _this.$message(myError.detail, "error");
};



</script>
<template>
  <div class="page-wbsj">

    <div class="c-titlebox">

      <span class="title">
      <span class="c-pointer" style="color: #909BA5;;margin-right: 5px;"
      @click="goback(null, $router, route.query.fpath || '/dataset/excel?id=' + route.query.id)">
        {{ route.query.name || 'EXCEL参数库' }}
        <span class="iconfont icon-xiangyoujiantou"></span>
      </span>
      添加EXCEL</span>
    </div>

    <div class="containbox c-bodybox" style="display: block;">
      <el-scrollbar>
      <div class="mg20">
        <div class="types">
          <span class="label">模板类型：</span>
          <div class="selbox">
            <el-select v-model="curtype" @change="typechange" filterable placeholder="Select" style="width: 300px">
              <el-option v-for="(key, val) in options" :key="val" :label="key" :value="val" />
            </el-select>
          </div>
        </div>

        <div class="uploadbox">
          <el-upload class="upload-demo" v-model:file-list="fileList"
            :headers="{ authorization: 'Bearer ' + store.state.token }" :before-upload="beforeAvatarUpload"
            :on-change="handleChange" :show-file-list="false" :on-error="errfn" :on-success="sucfn" :limit="15" multiple
            drag :action="actionurl">
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              点击或拖动文件到此处上传 <br />
              <div class="tip">
                支持 .xlsx 类型文件
                <br />最多支持 15 个文件。单个文件最大 100 MB。
              </div>
            </div>
          </el-upload>
        </div>
        <div v-show="fileList.length > 0" class="tablebox c-tablebox">
          <el-table :data="fileList" style="width: 100%">
            <el-table-column label="文件名">
              <template #default="scope">
                <div style="display: flex; align-items: center">
                  <span style="margin-left: 10px">{{ scope.row.name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="进度条">
              <template #default="scope">
                <el-progress
                  :percentage="scope.row.status == 'success' ? scope.row.percentage : Math.min(scope.row.percentage, 98)"
                  striped :color="customColorMethod" />
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
              <div class="c-emptybox"><icon type="empzwssjg" width="100" height="100"></icon>暂无数据~~</div>
            </template>
          </el-table>
        </div>
      </div>
    </el-scrollbar>
    </div>
  </div>
</template>
<style scoped>
.containbox {
  display: block;
}
.mg20{
  margin: 20px;
}

.containbox .types {
  display: flex;
  align-items: center;
  text-align: left;
}

.backbox .title {
  font-weight: bold;
  font-size: 16px;
}

.namebox {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  font-size: 16px;
  margin-bottom: 10px;
}

.btns {
  text-align: center;
  padding-top: 20px;
}

.page-wbsj {
  display: block;
  width: 100%;
  height: 100%;

}

.backbox {
  font-size: 16px;
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