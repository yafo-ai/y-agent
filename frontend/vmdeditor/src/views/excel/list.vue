<script setup>
import { ref, nextTick, shallowRef, onActivated, reactive } from "vue";
import { database, databaseDelete, databaseIndex, download,updatesxl } from "@/api/api";
import { useStore } from "vuex";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import icon from "@/components/icon.vue"

import { Search, UploadFilled } from "@element-plus/icons-vue";
const route = useRoute();
const router = useRouter();
const store = useStore();
const dialogFormVisible1 = ref(false);

let searchParams = reactive({
  page: 1,
  pagesize: 30,
  knowledgebase_id: route.query.id,
});

const total = ref(0);
const list = ref([]);

if (route.query.page) {
  searchParams.page = parseInt(route.query.page) || 1;
  searchParams.pagesize = parseInt(route.query.pagesize) || 30;
}

let pagelist = ref([]);

const search = (type) => {
  database(searchParams).then((res) => {
    let arr = res.rows || [];
    pagelist.value = arr;
    total.value = res.total_records;
  });
  if (type != "noquery") {
    let query = { ...route.query, ...searchParams };
    router.replace({ path: route.path, query: query });
  }
};

search();

const del = (id) => {
  _this.$confirm("此操作将永久删除该数据, 是否继续?").then((res) => {
    databaseDelete({ id }).then((res) => {
      _this.$message("删除成功");
      search();
    });
  });
};

const changeIndex = (id) => {
  databaseIndex({ id }).then((res) => {
    _this.$message("操作成功");
    search();
  });
};

// 创建知识库

import { goback, getTime } from "@/components/comp.js";

const downloadfn = (item) => {
  let src =
    window.location.href.split("/dataset/excel")[0] +
    "/api/filedatabase/download/" +
    item.id;
  download(src);
};
const tableRef = ref(null);
const updateList = () => {
  let params = {
    knowledgebase_id:route.query.id
  }
  updatesxl(params,true).then((res) => {
    if(res){
      _this.$message("批量更新向量库提交成功");
      search("init");
    } 
  })
  
}

const actionurl = ref("");

const editid = ref('');
const isShowEdit = ref(false);
const curfilename = ref('')
const editfn = (item) => {
  curfilename.value = item.file_name;
  editid.value = item.id;
  actionurl.value = "/api/filedatabase/update?id=" + item.id;
  isShowEdit.value = true;
}

const upload = ref(null);

const sucfn = (res, file, files) => {
  store.commit("loading", false);
  _this.$message("上传成功");
  isShowEdit.value = false;
  search();
  fileList.value = [];
  if(upload.value){
    upload.value.clearFiles();
  }
};
const errfn = (err) => {
  store.commit("loading", false);
  let myError = err.toString();
  myError = myError.replace("UploadAjaxError: ", "");
  myError = JSON.parse(myError);
  _this.$message(myError.detail, "error");
  if(upload.value){
    upload.value.clearFiles();
  }
};

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




</script>

<template>

  <div class="c-titlebox">
    <span class="title">
      <span class="c-pointer" style="color: #909BA5;;margin-right: 5px;"
        @click="goback(null, router, '/dataset/list?active=3')">
        全部知识库
        <span class="iconfont icon-xiangyoujiantou"></span>
      </span>
      {{ route.query.name || 'EXCEL参数库' }}</span>

    <div class="btns">
      <el-button size="small" @click="$router.push('/excel/add?id=' + searchParams.knowledgebase_id+'&name='+(route.query.name || 'EXCEL参数库'))"
        type="primary">添加EXCEL</el-button>
        <el-button size="small" @click="updateList()" plain>批量更新向量库</el-button>
        <el-link style="margin-left: 16px;" @click="download('/api/filedatabase/template')"> <span
          class="iconfont icon-anniu-xiazai"></span> 下载EXCEL模板</el-link>
    </div>
  </div>

  <div class="pagelistbox">
    <div class="tableboxContain c-tablebox">
        <el-table ref="tableRef" :data="pagelist" :max-height="store.getters.innerHeight - 141" style="width: 100%">
          <el-table-column width="80" type="index" label="编码" />

          <el-table-column label="模板">
            <template #default="scope">
              {{ scope.row.template_name }}
            </template>
          </el-table-column>

          <el-table-column label="文件名称">
            <template #default="scope">
              {{ scope.row.file_name }}
            </template>
          </el-table-column>

          <el-table-column align="center" label="日期">
            <template #default="scope">
              {{
                getTime(scope.row.updated_at) 
              }}
            </template>
          </el-table-column>
          <!-- <el-table-column label="index创建时间">
            <template #default="scope">
              {{
                getTime(scope.row.index_at)
              }}
            </template>
          </el-table-column>

          <el-table-column label="是否已经添加到向量">
            <template #default="scope">
              {{ scope.row.is_index ? "是" : "否" }}
            </template>
          </el-table-column> -->

         

          <el-table-column label="文件大小">
            <template #default="scope">
              {{ scope.row.file_size }}
            </template>
          </el-table-column>

          <el-table-column width="360" align="right" label="操作">
            <template #default="scope">

              <div @click="editfn(scope.row)" class="c-table-ibtn">
                    <span class="iconfont icon-xiugai"></span>
                    修改
                  </div>

              <div @click="changeIndex(scope.row.id)" :style="scope.row.index_at?'color:var(--el-color-primary)':''"  class="c-table-ibtn">
                <span class="iconfont icon-liebiao-gengxinxiangliang"></span>
                <span style="display: flex;align-items: center;">{{
                  scope.row.index_at ? "更新向量" : "添加向量"
                }}</span>
              </div>



              <div @click="downloadfn(scope.row)" class="c-table-ibtn">
                <span class="iconfont icon-anniu-xiazai"></span>
                下载
              </div>

              <div @click="
                $router.push({
                  path: '/excel/detail',
                  query: { id: scope.row.id, fpath: route.fullPath },
                })
                " class="c-table-ibtn">
                <span class="iconfont icon-liebiao-chakan"></span>
                查看
              </div>

              <div @click="del(scope.row.id)" class="c-table-ibtn c-btn-del">
                <span class="iconfont icon-shuzhuang-shanchu"></span>
                删除
              </div>
            </template>
          </el-table-column>
          <template #empty="scope">
            <div class="c-emptybox"><icon type="empzwssjg" width="100" height="100"></icon>暂无数据~~</div>
          </template>
        </el-table>

        <div v-if="total > 0" class="c-pagination">
          <el-pagination :hide-on-single-page="false" background :page-size="searchParams.pagesize"
            :current-page="searchParams.page" @size-change="
              (val) => {
                searchParams.pagesize = val;
                searchParams.page = Math.min(
                  Math.ceil(total / searchParams.pagesize),
                  searchParams.page
                );
                search();
              }
            " @current-change="
              (val) => {
                searchParams.page = val;
                tableRef && tableRef.scrollTo(0,0)
                search();
              }
            " :page-sizes="[30, 50, 100, 900]" layout="total,sizes,jumper,prev, pager, next" :total="total" />
        </div>
    </div>
  </div>


  <el-dialog align-center v-model="isShowEdit" title="修改文件" width="800">
    <div class="filename" style="    text-align: left;
    margin-bottom: 10px;
    font-weight: bold;
">文件名称：{{ curfilename }}</div>
    <div class="uploadbox">
          <el-upload class="upload-demo" ref="upload" v-model:file-list="fileList"
            :headers="{ authorization: 'Bearer ' + store.state.token }" :before-upload="beforeAvatarUpload"
            :on-change="handleChange" :show-file-list="false" :on-error="errfn" :on-success="sucfn" :limit="1" multiple
            drag :action="actionurl">
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div style="display: flex; align-items: center;flex-wrap: wrap;" class="el-upload__text">
              <div style="text-align: left; margin: 0 auto;" class="tip">
                选择要修改的Excel文件,支持 .xlsx 类型文件 <br>
                Excel数据修改规则:<br>
1、Excel数据修改，必须全量上传。<br>
2、严格按照新Exce数据中的"唯一编码"进行新增、修改、删除操作。<br>
3、修改后需要重新向量化。 <br>
                
              </div>
            </div>
          </el-upload>
        </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button plain @click="isShowEdit=false;">取消</el-button>
       
      </div>
    </template>
  </el-dialog>
</template>
<style scoped>
.backbox {
  padding: 20px 0 0 20px;
  font-size: 20px;
}

.icon-zhishiku {
  color: var(--el-color-primary);
}

.icon-zhishikuguanli {
  color: var(--el-color-success);
}

.listbox {
  display: block;
  text-align: center;
}

.listbox .icon-Excel {
  font-size: 20px;
}

.tableboxContain {
  width: 100%;
  height: auto;
}

.pagelistbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  flex-wrap: wrap;
  padding: 0;
  width: 100%;
  box-sizing: border-box;
  height: 100%;
}

.pagelistbox .item {
  width: 400px;
  height: 150px;
  background: #fff;
  border-radius: 10px;
  box-sizing: border-box;
  margin: 10px;
  cursor: pointer;
  border: 1px solid #eee;
  padding: 10px 10px 40px 20px;
  position: relative;
}

.pagelistbox .item:hover {
  border: 1px solid var(--el-color-primary);
}

.pagelistbox .item .c-dataset-btns {
  text-align: left;
}

.namebox {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.namebox .rbox {
  flex-shrink: 0;
}

.namebox .lbox {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  font-size: 16px;
}

.namebox .lbox .iconfont {
  flex-shrink: 0;
  font-size: 20px;
  margin-right: 5px;
}

.name {
  word-break: break-all;
}



.icon-shugui {
  color: var(--chakra-colors-primary-600);
  font-size: 20px;
}
</style>
