<script setup>
import { ref, nextTick, reactive, watch } from "vue";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import { useStore } from "vuex";
import {
  workflowdelete,
  workflow,
  add_update,
  promptsversionsDetail,
  download,
  workflowcopy,
  categorytree,
  categorydelete,
  categoryadd,
  mcp_providerlist,
  workflowget,
} from "@/api/api";
import { goback, getTime } from "@/components/comp.js";
import { v4 as uuidv4 } from "uuid";
import icon from "@/components/icon.vue"
const route = useRoute();
const router = useRouter();
const category_id = ref(undefined);
const props = defineProps({
  proType: {
    type: [String, Number],
    default: () => "",
  },
  isCheck: {
    type: [Boolean],
    default: () => false,
  },
  checkList: {
    type: [Array],
    default: () => [],
  },
});

const store = useStore();
const dialogFormVisible1 = ref(false);

let pagelist = ref([]);
const total = ref(0);

const page = ref(1);
const pagesize = ref(36);

if (route.query.page) {
  page.value = parseInt(route.query.page);
}
if (route.query.pagesize) {
  pagesize.value = parseInt(route.query.pagesize);
}
if (route.query.category_id) {
  category_id.value = parseInt(route.query.category_id);
}
const search = (type) => {
  let params = { page: page.value, pagesize: pagesize.value, category_id: category_id.value };
  if (type == "init") {
    params.page = 1;
  }
  workflow(params).then((res) => {
    let arr = res.rows || [];
    if (props.proType) {
      arr = res || [];
      total.value = 0;
    } else {
      total.value = res.total_records;
    }
    pagelist.value = arr;
  });

  if (type != "noquery") {
    let query = { ...route.query, ...params };
    router.replace({ path: route.path, query: query });
  }
};

search("noquery");

const emits = defineEmits(["subfn"]);
const checkItem = (item) => {

  router.push({ path: "/flow", query: { id: item.id, api_key: item.api_key } });
};

const openDialog = async (item) => {
  resetForm();

  if (item) {
    let resitem = await workflowget({ id: item.id });
    setFormValues(resitem);
  }
  dialogFormVisible1.value = true;
  focusOnInput();
};

const resetForm = () => {
  form1.id = 0;
  form1.name = "";
  form1.category_id = category_id.value;
  form1.category_name = "";
  form1.is_tool = false;
  form1.use_log = true;
  form1.sources = [];
  form1.is_share = false;
  form1.api_key = undefined;
  form1.caption = "";
  form1.view_json = "";
};

const setFormValues = (item) => {
  form1.id = item.id;
  form1.name = item.name;
  form1.category_id = item.category_id;
  form1.category_name = item.category_name;
  form1.is_share = item.is_share;
  form1.api_key = item.api_key;
  form1.sources = item.sources || [];
  form1.is_tool = item.is_tool;
  form1.use_log = item.use_log === undefined ? true : item.use_log;
  form1.caption = item.caption;
  form1.view_json = item.view_json;
};


const focusOnInput = () => {
  setTimeout(() => {
    const inputElement = document.querySelector(".autofocus.inp2 input");
    if (inputElement) {
      inputElement.focus();
    }
  }, 100);
};

const del = (id) => {
  _this.$confirm("此操作将永久删除该工作流, 是否继续?").then((res) => {
    workflowdelete({ id }).then((res) => {
      _this.$message("删除成功");
      search();
    });
  });
};

// 创建知识库
const form1 = reactive({
  name: "",
  content: "",
  category_id: undefined,
  category_name: "",
  is_tool: false,
  is_share: false,
  use_log: true,
  api_key: undefined,
  sources: [],
  id: 0,
  view_json: "",
});
const ruleFormRef1 = ref();
const rules1 = reactive({
  name: [{ required: true, message: "请输入流程图名称" }],
});
const saveZsk = async (formEl) => {
  if (!formEl) return;
  formEl.validate((valid) => {
    if (valid) {
      form1.category_id = form1.category_id || 0;
      findAndAddCategory(dataSource.value, form1.category_id, (category) => {
        form1.category_name = category.name;
      })

      add_update(form1, 'baseinfo').then((res) => {
        if (res) {
          _this.$message("提交成功");
          dialogFormVisible1.value = false;
          // if (res.id) {
          //   router.push({ path: "/flow", query: { id: res.id } });
          // }
          search();
          // if (!form1.id) {
          //   // 新增成功后，跳转到流程编辑页面
          //   router.push({ path: "/flow", query: { id: res.id } });
          // }
        }
      });
    } else {
      document.querySelectorAll(".autofocus.inp2 input")[0].focus();
      return false;
    }
  });
};

const copyfn = (item, curapi_key) => {
  if (!item.is_share) {
    _this.$message("此流程不支持分享，请先设置后再进行操作！", "error");
    return;
  }
  let id = item.id;
  let api_key = curapi_key || '';
  _this.$copy(
    window.location.href.split("/flowlist")[0] + "/flowshare?id=" + id + "&api_key=" + api_key
  );
};

const tableRef = ref(null);



const copyflow = (item) => {
  workflowcopy({ flow_id: item.id }).then((res) => {
    _this.$message("复制成功");
    search();
  });
}

const delConfirmFn = async (txt, fn) => {
  let cfm = await _this.$confirm(txt);
  if (cfm) {
    fn && fn();
  }
};


const upload = ref(null);

const sucfn = (res, file, files) => {
  console.log(res, file, files)
  store.commit("loading", false);
  _this.$message("上传成功");
  search();
  fileList.value = [];
  if (upload.value) {
    upload.value.clearFiles();
  }
};
const errfn = (err) => {
  store.commit("loading", false);
  let myError = err.toString();
  myError = myError.replace("UploadAjaxError: ", "");
  myError = JSON.parse(myError);
  _this.$message(myError.detail, "error");
  if (upload.value) {
    upload.value.clearFiles();
  }
};

const fileList = ref([]);
const handleChange = (uploadFile, uploadFiles) => {
  console.log(uploadFile, uploadFiles);
  fileList.value = uploadFiles;
};



const beforeAvatarUpload = (file) => {
  // if (/\.(json)$/i.test(file.name)) {
  // } else {
  //   _this.$message("上传的文件格式不正确", "error");
  //   return false;
  // }
  store.commit("loading", true);

  return true;
};



const dataSource = ref([]);
const treeSelect = ref(null);

const checkType = async (item) => {
  category_id.value = item.id;
  search("init");
};

const searchCate = (params) => {
  categorytree()
    .then(async (res) => {
      dataSource.value = res || [];
      await nextTick();
      treeSelect.value.setCurrentKey(parseInt(category_id.value));
    })
    .catch((err) => {
      // if (err.response.data && err.response.data.detail == "知识库类目不存在") {
      //   dataSource.value = [];
      // }
    });
};
searchCate();
const isShowAdd = ref(false);
const addparam = reactive({ name: "", id: 0, note: "", pid: 0 });



// 使用函数
const addTypefn = async (item, type) => {
  addparam.pid = item.pid || 0;
  addparam.id = item.id || 0;
  addparam.name = item.name || "";
  addparam.note = item.note || "";
  if (type == "child") {
    // 添加子节点
    addparam.pid = item.id;
    addparam.name = "";
    addparam.note = "";
    addparam.id = undefined;
  }
  isShowAdd.value = true;
  setTimeout(() => {
    inputRef.value.focus();
  }, 500);
};

const delTypefn = (item) => {
  _this.$confirm("确定要删除所选数据?").then(() => {
    categorydelete({ id: item.id }).then((res) => {
      _this.$message("删除成功");
      searchCate();
    });
  });
};


const inputRef = ref(null);
const subaddfn = () => {


  if (!addparam.name) {
    inputRef.value.focus();
    return false;
  }
  categoryadd(addparam)
    .then((res) => {
      isShowAdd.value = false;
      searchCate();
      _this.$message("操作成功");
    })
    .catch((err) => { });
};


const findAndAddCategory = (categories, parentId, fn) => {
  // 递归查找类型名称
  categories.forEach((category) => {
    if (category.id === parentId) {
      fn && fn(category);
      return true;
    }

    if (category.children && category.children.length > 0) {
      findAndAddCategory(category.children, parentId, fn);
    }
  });
};



</script>

<template>
  <div class="c-titlebox">
    <span class="title">流程图</span>
    <div class="btns">
      <el-button style="margin-right: 16px;" size="small" @click="openDialog()" type="primary">新建</el-button>
      <el-upload style="width: 100%;" class="upload-demo" ref="upload" v-model:file-list="fileList"
        :show-file-list="false" :headers="{ authorization: 'Bearer ' + store.state.token }"
        :before-upload="beforeAvatarUpload" :on-change="handleChange" :on-error="errfn" :on-success="sucfn"
        action="/api/workflow/import">
        <el-button size="small" plain>导入流程</el-button>
      </el-upload>
    </div>
  </div>

  <div class="c-bodybox">
    <div class="catebox leftbox">
      <div class="topbtns">
        <span class="title">流程图分类</span>
        <el-button @click="checkType({ id: undefined })" class="on noradius" plain>
          <span class="iconfont icon-anniu-zhankai"></span>
          查看全部
        </el-button>

      </div>
      <div class="contain">
        <el-scrollbar>
          <div class="el-tree el-tree--highlight-current" role="tree" style="width: 100%">
            <div class="el-tree-node" :class="{ 'is-current': category_id == 0 }">
              <div class="el-tree-node__content">
                <div @click="checkType({ id: 0 })" style="padding-left: 35px" class="custom-tree-node">
                  <div class="item">
                    未分类
                  </div>
                </div>
              </div>
            </div>
          </div>
          <el-tree ref="treeSelect" style="width: 100%" :data="dataSource" node-key="id" empty-text="暂无数据"
            highlight-current :current-node-key="category_id ? parseInt(category_id) : undefined" default-expand-all
            @node-click="checkType" :expand-on-click-node="false">
            <template #default="{ node, data }">
              <div :title="data.name" class="custom-tree-node">
                <div class="item">
                  <p class="ellipsis">{{ data.name }}</p>
                </div>
                <div class="btns">
                  <span title="添加子类目" @click.stop="addTypefn(data, 'child')"
                    class="iconfont icon-shuzhuang-tianjia"></span>
                  <span title="修改" @click.stop="addTypefn(data)" class="iconfont icon-xiugai"></span>
                  <span title="删除类目" @click.stop="delTypefn(data)" class="iconfont icon-shuzhuang-shanchu"></span>
                </div>
              </div>
            </template>
          </el-tree>
        </el-scrollbar>
      </div>

      <div class="botbtns">
        <el-button style="width: 100%;" plain class="on noradius" @click="addTypefn({ id: 0 })"><span
            class="iconfont icon-liebiao-xinzeng"></span> 新增分类</el-button>
      </div>
    </div>


    <div style="height: auto;" class="scrollbox rightbox">
      <el-scrollbar :max-height="store.getters.innerHeight - 186" ref="tableRef">
        <div class="contain">
          <div v-if="pagelist.length < 1" class="c-emptybox">
            <icon type="empzwssjg" width="100" height="100"></icon>
            该分类下暂无数据
          </div>
          <div class="pagelistbox">
            <div v-for="(item, index) in pagelist" @click="checkItem(item, index)" :key="index" class="item"
              :class="{ active: item.checked, ['id' + item.id]: true }">
              <span class="iconfont icon-liuchengtu-kapianzaiti"></span>
              <div class="topbox">
                <div v-if="item.is_tool" class="iconbtn re tool"></div>
                <div v-else class="iconbtn re"></div>
                <div @click.stop class="rbox">
                  <el-popover :width="160">
                    <template #reference>
                      <span class="iconfont icon-gengduo c-cardbtn-icon"></span>
                    </template>
                    <template #default>
                      <div class="c-cardbtn-btns">
                        <div @click="openDialog(item)" class="item">
                          <span class="name">设置</span>
                        </div>


                        <div @click="del(item.id)" class="item err">
                          <span class="name">删除</span>
                        </div>

                        <div title="创建一个流程图副本" @click="copyflow(item)" class="item">
                          <span class="name">创建副本</span>
                        </div>

                        <div title="导出文件" @click="download('/api/workflow/export/' + item.id)" class="item">
                          <span class="name">导出文件</span>
                        </div>
                      </div>
                    </template>
                  </el-popover>
                </div>
              </div>


              <div :title="item.name" class="namebox re ellipsis">
                {{ item.name }}
              </div>

              <div :title="item.caption || '这个流程图还没有介绍~'" class="introbox re ellipsis2">
                {{ item.caption || "这个流程图还没有介绍~" }}
              </div>

              <div class="sharebtn">
                编辑
              </div>

              <div v-if="item" class="ellipsis labelbox">
                <template v-if="item.sources && item.sources.length > 0">
                  <el-popover placement="bottom-start"
                    :popper-style="{ width: 'auto', padding: '10px', minWidth: '80px', maxWidth: '600px' }">
                    <template #reference>
                      <div class="ellipsis">
                        分享
                      </div>
                    </template>
                    <template #default>
                      <div class="sourcesbox">
                        <div v-for="citem in item.sources" class="item">
                          <div class="name"><span>名称：{{ citem.source_name }}</span> <el-link
                              @click.stop="copyfn(item, citem.api_key)">分享</el-link></div>
                          <div class="api_key">api_key：{{ citem.api_key }} </div>
                        </div>
                      </div>
                    </template>
                  </el-popover>
                </template>
                
              </div>
            </div>
          </div>
        </div>
      </el-scrollbar>
      <div v-if="total > 0" style="padding-right: 24px;" class="c-pagination">
        <el-pagination :hide-on-single-page="false" background :page-size="pagesize" :current-page="page" @size-change="
          (val) => {
            pagesize = val;
            page = Math.min(Math.ceil(total / pagesize), page);
            search();
          }
        " @current-change="
          (val) => {
            page = val;
            tableRef && tableRef.scrollTo(0, 0)
            search();
          }
        " :page-sizes="[30, 50, 100, 900]" layout="total,sizes,jumper,prev, pager, next" :total="total" />
      </div>
    </div>

  </div>

  <el-dialog align-center v-model="dialogFormVisible1" :title="form1.id ? '设置流程图' : '创建流程图'" width="900">
    <div class="dialogFormVisible1box">
      <el-scrollbar>
        <div class="formbox">
          <el-form ref="ruleFormRef1" :rules="rules1" :label-width="auto" label-position="top" inline :model="form1">
            <el-form-item style="width: calc(100% - 316px);margin-right: 16px;" label="流程图名称" prop="name">
              <el-input class="autofocus inp2" placeholder="请输入流程图名称" v-model="form1.name" maxlength="50"
                autocomplete="off" />
            </el-form-item>
            <el-form-item label="流程图类型" style="width: 300px;margin-right: 0;" prop="prompt_type_id">

              <el-tree-select v-model="form1.category_id" filterable check-strictly :node-key="'id'"
                :props="{ children: 'children', label: 'name', value: 'id' }" :default-expand-all="true"
                :check-on-click-node="true" :data="[{
                  id: 0, name: '未分类', pid: null, children:
                    []
                }].concat(dataSource)" style="width: 100%">
                <template #default="{ node, data }">
                  <span>{{ data.name }}</span>
                </template>
              </el-tree-select>
            </el-form-item>

            <el-form-item class="c-switchbox-label"
              style="width: calc(33% - 16px);margin-right: 16px;margin-top: -26px;" label="" prop="is_tool">
              <template #label>是否工具
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark" content="开启后，可以在流程编辑页面，将此流程作为工具使用"
                  placement="top">
                  <span style="position: relative;top: 1px;" class="iconfont icon-bangzhu"></span>
                </el-tooltip>
              </template>
              <div class="c-switchbox">
                <div class="label">
                </div>
                <div class="switch">
                  <el-switch v-model="form1.is_tool" inline-prompt active-text="是" inactive-text="否" />
                </div>
              </div>
            </el-form-item>

            <el-form-item class="c-switchbox-label"
              style="width: calc(33% - 16px);margin-right: 16px;margin-top: -26px;" label="" prop="use_log">
              <template #label>是否启用日志
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark" raw-content
                  content="开启后，系统默认会记录此流程的运行日志 <br /> 注意:此开关仅作为默认设置，当通过WebApi调用此流程的时候，可以单独指定是否启用日志" placement="top">
                  <span style="position: relative;top: 1px;" class="iconfont icon-bangzhu"></span>
                </el-tooltip>
              </template>
              <div class="c-switchbox">
                <div class="label">
                </div>
                <div class="switch">
                  <el-switch v-model="form1.use_log" inline-prompt active-text="是" inactive-text="否" />
                </div>
              </div>
            </el-form-item>

            <el-form-item class="c-switchbox-label" style="width: calc(34% - 0px);margin-right: 0;margin-top: -26px;"
              label="" prop="is_share">
              <template #label>是否允许分享
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark" raw-content
                  content="允许外部进行 网页访问 和 WebApi调用" placement="top">
                  <span style="position: relative;top: 1px;" class="iconfont icon-bangzhu"></span>
                </el-tooltip>
              </template>
              <div class="c-switchbox">
                <div class="label">
                </div>
                <div class="switch">
                  <el-switch v-model="form1.is_share" inline-prompt active-text="是" inactive-text="否" />
                </div>
              </div>
            </el-form-item>





            <el-form-item style="width: 100%;margin-right: 0;position: relative;" label="api_key" prop="caption">
              <template #label>分享设置
                <!-- <el-tooltip popper-class="c-flowtip" class="item" effect="dark" content="用于外部调用此流程安全验证的，访问密钥"
                placement="top">
                <span style="position: relative;top: 1px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip> -->
                <el-button style="position: absolute;right: 0;top: 0;"
                  @click="form1.sources.push({ source_id: 0, source_name: '', api_key: uuidv4() })" size="small"
                  type="primary">新增</el-button>
              </template>

              <div class="tagsbox">
                <div class="item title">
                  <div class="name">名称</div>
                  <div class="api_key">api_key</div>
                  <div class="opt"></div>
                </div>
                <div v-for="(citem, cindex) in form1.sources" class="item">
                  <div class="name">
                    <el-input style="width: 100%;" v-model="citem.source_name" placeholder="标签名称"></el-input>
                  </div>
                  <div class="api_key">
                    <el-input v-model="citem.api_key" placeholder="api_key"></el-input>
                  </div>
                  <div class="opt">
                    <span @click="form1.sources.splice(cindex, 1)" class="iconfont icon-liebiao-shanchu"></span>
                  </div>
                </div>
              </div>

            </el-form-item>



            <el-form-item style="width: 100%;margin-right: 0;" label="流程图介绍" prop="caption">
              <el-input v-model="form1.caption" :rows="10" type="textarea" placeholder="这个流程图还没有介绍~" />
            </el-form-item>



          </el-form>
        </div>
      </el-scrollbar>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogFormVisible1 = false" plain>取消</el-button>
        <el-button type="primary" @click="saveZsk(ruleFormRef1)">
          提交
        </el-button>
      </div>
    </template>
  </el-dialog>

  <el-drawer v-model="isShowAdd" :title="addparam.id ? '修改分类' : '新增分类'" size="600px">
    <div class="formbox">
      <el-form ref="formRef" style="width: 100%;" :model="addparam" @submit.native.prevent
        @keyup.native.enter.prevent="subaddfn()" label-width="auto" class="demo-dynamic">
        <el-form-item prop="name" label=" " :rules="[
          {
            required: true,
            message: '请输入分类名称',
            trigger: 'blur',
          },
        ]">
          <el-input v-model="addparam.name" ref="inputRef" placeholder="分类名称" />
        </el-form-item>
      </el-form>
    </div>
    <div class="dialog-footer">
      <el-button plain @click="isShowAdd = false"> 取消 </el-button>
      <el-button type="primary" @click="subaddfn()"> 确定 </el-button>
    </div>
  </el-drawer>

  <!-- 新建文件夹 -->
</template>

<style scoped>
.sourcesbox {
  display: block;
  width: 100%;
}

.sourcesbox .item {
  display: block;
  text-align: left;
  font-size: 12px;
  padding-bottom: 10px;
  cursor: pointer;
}

.sourcesbox .item .name {
  color: #333;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: nowrap;
  width: 100%;
}

.sourcesbox .item .api_key {
  color: #999;
}

.labelbox {
  display: block;
  text-align: left;
}

.pagelistbox .item .labelbox {
  position: absolute;
  left: 24px;
  bottom: 16px;
  color: var(--el-color-primary);
}

.pagelistbox .item .labelbox .brand_name {
  margin-right: 5px;
}

.tagsbox {
  display: block;
  width: 100%;
}

.tagsbox .item {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.tagsbox .item.title {
  background: #f1f1f1;
}

.tagsbox .item.title .api_key,
.tagsbox .item.title .name {
  padding-left: 10px;
}

.tagsbox .item .name {
  width: calc(50% - 58px);
  text-align: left;
  box-sizing: border-box;
}

.tagsbox .item .api_key {
  width: calc(50% - 58px);
  text-align: left;
  box-sizing: border-box;
}

.tagsbox .item .opt {
  width: 80px;
  text-align: center;
  cursor: pointer;
}

.c-switchbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.c-switchbox .label {
  font-size: 14px;
  color: #999;
}

.scrollbox {
  height: auto;
  /* background: linear-gradient(136deg, #EEF8FF 0%, rgba(238, 248, 255, 0.4) 50%, #F8F8F8 100%); */
}

.sharebtn {
  display: block;
  position: absolute;
  right: 0;
  bottom: 0;
  width: 56px;
  height: 56px;
  background: #eff4fd;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 100%;
  color: var(--c-font-color);
}

.sharebtn .iconfont {
  font-size: 20px;
  color: #999;
}

.sharebtn:hover {
  opacity: 0.8;
}



.dialogFormVisible1box {
  display: block;
  height: 600px;
  margin: 0 -16px;
}

.dialogFormVisible1box .formbox {
  text-align: left;
  margin: 0 16px;
}

.historybox .title1 {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
}

.icon-zhishiku {
  color: var(--el-color-primary);
}

.icon-zhishikuguanli {
  color: var(--el-color-success);
}

.icon-damoxing {
  font-size: 36px;
  font-weight: bold;
  color: #1948e7;
}

.topbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-right: 60px;
}

.listbox {
  display: block;
  text-align: center;
}

.listbox .icon-damoxing {
  font-size: 20px;
}

.pagelistbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  flex-wrap: wrap;
}

.pagelistbox .item {
  width: 310px;
  height: 216px;
  margin: 0px 16px 16px 0;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
  padding: 24px;
  border: 1px solid transparent;
}

.pagelistbox .item .icon-liuchengtu-kapianzaiti {
  position: absolute;
  left: 0;
  top: -54px;
  z-index: 0;
  font-size: 216px;
  color: #eff4fd;
}

.pagelistbox .item>* {
  z-index: 1;
}

.pagelistbox .item .re {
  position: relative;
}

.pagelistbox .iconbtn {
  display: block;
  width: 40px;
  height: 40px;
  background: url(@/assets/imgs/notool.png) no-repeat top left;
  background-size: 40px 40px;
}

.pagelistbox .iconbtn.tool {
  background-image: url(@/assets/imgs/tool.png);
}

.pagelistbox .item.active {
  border: 1px solid var(--el-color-success);
}

.pagelistbox .item .c-dataset-btns {
  text-align: left;
}

.namebox {
  display: block;
  box-sizing: border-box;
  padding: 16px 0;
  text-align: left;
  color: #333333;
  font-size: 20px;
  font-weight: 500;
}

.namebox.type2 {
  background: #f4fbf3;
}

.namebox.type3 {
  background: #fffaf4;
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

.namebox .lbox .name {
  text-align: left;
  display: inline-block;
  width: 310px;
}

.name {
  word-break: break-all;
}

.introbox {
  word-break: break-all;
  text-align: left;
  color: #949494;
  font-size: 12px;
  width: 204px;
}

.botbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: absolute;
  left: 20px;
  bottom: 10px;
  right: 20px;
  height: 30px;
  font-size: 14px;
}

.botbox .rbox .bitem {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  background: var(--chakra-colors-myGray-100);
  border: 1px solid var(--chakra-colors-myGray-200);
  border-radius: var(--chakra-radii-md);
  padding: 0px 10px;
}

.botbox .rbox .bitem .iconfont {
  color: #333;
}

.icon-shugui {
  color: var(--chakra-colors-primary-600);
  font-size: 20px;
}
</style>
