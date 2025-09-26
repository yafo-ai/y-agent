<script setup>
import { ref, reactive, nextTick } from "vue";
import {
  platformlist,
  shopdelete,
  shopadd,
  shoplist,
  categoriesadd,
  categoriesdelete,
  profileadd,
  profilepaged,
  profiledelete,
  goodsadd,
  goodsdetail,
  goodsdelete,
  goodspaged,
  categorieslist,
  download,
} from "@/api/api";

import { copyData } from "@/assets/utils/util";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";
import { goback, getTime } from "@/components/comp.js";
import { cloneDeep } from "lodash";
import icon from "@/components/icon.vue"
const route = useRoute();
const router = useRouter();
const store = useStore();

let searchParams = reactive({
  page: 1,
  pagesize: 30,
  active: '1',
  name: '',
  goods_code: '',
  barcode: '',
  category_id: undefined,
  category_name: '',
  recommend_flag: undefined,
  on_sale_flag: undefined,
  is_empty_profile: undefined,
  suite_flag: undefined,
  shop_id: undefined,
  sku: '',
});
const total = ref(0);



let pagelist = ref([]);

const initSearchParams = (type) => {
  // 初始化分页参数为第一页
  searchParams.page = 1;
  searchParams.name = '';
  searchParams.goods_code = '';
  searchParams.barcode = '';

  searchParams.category_name = '';

  searchParams.sku = '';

  if (searchParams.active == 2) {
    searchParams.shop_id = undefined;


  }
  if (searchParams.active == 1) {
    searchParams.category_id = undefined;
    searchParams.recommend_flag = undefined;
    searchParams.on_sale_flag = undefined;
    searchParams.suite_flag = undefined;
    searchParams.is_empty_profile = undefined;
  }
};

const curprofile_code = ref('');



const searchAddlist = () => {
  if (!curprofile_code.value) return false;
  let params = {
    page_index: 1,
    pagesize: 10000,
    profile_code: curprofile_code.value,
    barcode: '',
    name: '',
    category_id: undefined,
  }
  profilepaged(params).then((res) => {
    let arr = res.rows || [];
    if (arr.length == 0) {
      _this.$message('没有找到相关商品', 'warning');
      return false;
    }

    arr.forEach(item => {
      item.quantity = 1;
      let cindex = -1;
      form.value.profile_tuple.forEach((item2, index) => {
        if (item2.id == item.id) {
          cindex = index;
        }
      });
      if (cindex === -1) {
        // 如果不存在 添加进去
        form.value.profile_tuple.push(item);
      } else {
        _this.$message('商品已存在，请勿重复添加', 'warning');
      }
    });
    // form.value.profile_tuple = form.value.profile_tuple.concat(arr);
    initTz();
    curprofile_code.value = '';
  });
};


const search = async (type) => {
  if (type === "init") {
    searchParams.page = 1;
  }

  if (type !== "noquery") {
    router.replace({
      path: route.path,
      query: { ...route.query, ...searchParams }
    });
  }

  try {
    const params = {
      page_index: searchParams.page,
      pagesize: searchParams.pagesize,
      ...(searchParams.active == 1 ? {
        category_id: searchParams.category_id,
        sku: searchParams.sku,
        goods_code: searchParams.goods_code || undefined,
        shop_id: searchParams.shop_id,
        recommend_flag: searchParams.recommend_flag,
        on_sale_flag: searchParams.on_sale_flag,
        suite_flag: searchParams.suite_flag,
        is_empty_profile: searchParams.is_empty_profile
      } : {
        goods_code: searchParams.goods_code || undefined,
        barcode: searchParams.barcode,
        name: searchParams.name,
        category_id: searchParams.category_id
      })
    };

    const res = await (searchParams.active == 1 ? goodspaged(params) : profilepaged(params));
    pagelist.value = res.rows || [];
    total.value = res.total;
  } catch (error) {
    console.error('Search error:', error);
  }
};

copyData(searchParams, route.query, 'shop_id');
search("noquery");

const scrollbarRef = ref(null);

const delTypefn = (item) => {
  _this.$confirm("确定要删除所选条目吗?").then((res) => {
    if (searchParams.active == 2) {
      categoriesdelete({ id: item.id }).then((res) => {
        _this.$message("删除成功");
        searchCate();
      })
    } else {
      shopdelete({ id: item.id }).then((res) => {
        _this.$message("删除成功");
        shoplistfn();
      })

    }

  });
};

const delfn = (item) => {
  _this.$confirm("确定要删除商品吗，删除后将无法识别商品链接，此操作不可恢复!").then((res) => {
    if (searchParams.active == 2) {

      profiledelete({ id: item.id }).then((res) => {
        _this.$message("删除成功");
        search();
      })
    } else {
      goodsdelete({ id: item.id }).then((res) => {
        _this.$message("删除成功");
        search();
      })
    }

  });
};
const isShowCompDetail = ref(false);



const initializeForm = (type) => {
  if (type == 1) {
    return {
      id: 0,  // 主键ID
      pid: undefined,  // 父级ID
      platform_id: "",  // 平台ID
      shop_name: "",  // 插件名称
    };
  } else {
    return {
      id: 0,  // 主键ID
      shop_id: undefined,  // 店铺ID
      category_id: undefined,  // 店铺名称
      sku: "",
      suite_flag: false,
      recommend_flag: false,
      on_sale_flag: true,
      price: 0,
      sale_point: "",
      goods_name: "",
      goods_code: "",
      barcode: "",
      profile_tuple: [],  // 关联档案
    };
  }

};

const ruleFormRef = ref(null);
const form = ref(initializeForm());
const addfn = async (item) => {
  form.value = initializeForm()
  if (item) {
    if (searchParams.active == 2) {
      item.goods_name = item.name;

      form.value = cloneDeep(item);
    } else {
      let res = await goodsdetail({ id: item.id });
      res.category_id = res.goods_category_id
      res.profiles.forEach(item => {
        item.id = item.profile_id;
      });
      res.profile_tuple = res.profiles || [];
      delete res.profiles;

      form.value = res;
    }

  }

  isShowCompDetail.value = true;

  if (ruleFormRef.value) {
    ruleFormRef.value.clearValidate()
  }
};

const dialogFormVisible = ref(false)
const addFormRef = ref(null)
const addparam = ref(initializeForm(1))

const profileaddfn = (params) => {
  profileadd(params).then(async (res) => {
    if (res.is_forced_commit) {
      let cfm = await _this.$confirm('此商品已经配置到店铺商品，是否强制修改？', '提示');
      if (cfm) {
        params.is_forced_commit = true;
        profileaddfn(params);
        return;
      }
    } else {
      _this.$message("保存成功");
      search();
      isShowCompDetail.value = false;
    }

  });
};


const sub = (formEl) => {
  if (!formEl) return
  formEl.validate((valid) => {
    if (valid) {
      let params = cloneDeep(form.value);
      if (searchParams.active == 2) {
        params = {
          id: form.value.id,
          goods_name: form.value.goods_name,
          goods_code: form.value.goods_code,
          barcode: form.value.barcode,
          category_id: form.value.category_id,
        }
        params.is_forced_commit = undefined;
        profileaddfn(params);
      } else {
        let arr = [];
        form.value.profile_tuple.forEach(item => {
          arr.push([(item.id || item.profile_id), item.quantity, item.mapping_id || 0])
        })

        params.profile_tuple = arr;
        delete params.barcode;
        delete params.goods_code;
        delete params.goods_name;
        goodsadd(params).then((res) => {
          _this.$message("保存成功");
          search();
          isShowCompDetail.value = false;
        });
      }


    }
  })
};











const handleClick = (tab, event) => {

  initSearchParams();
  search('init');
};


// 新增弹窗


const addshop = (formEl) => {
  if (!formEl) return
  formEl.validate((valid) => {
    if (valid) {
      let params = {};
      if (searchParams.active == 2) {
        params = { parent_id: addparam.value.pid, id: addparam.value.id, name: addparam.value.shop_name };
        categoriesadd(params).then((res) => {
          _this.$message("保存成功");
          searchCate();
          dialogFormVisible.value = false;
        });
      } else {
        params = { platform_id: addparam.value.platform_id, id: addparam.value.id, shop_name: addparam.value.shop_name };
        shopadd(params).then((res) => {
          _this.$message("保存成功");
          shoplistfn();
          dialogFormVisible.value = false;
        });
      }


    }
  })
};
/**
 * 将页面上的第一个输入框设置为焦点
 */
const focus = () => {
  setTimeout(() => {
    if (document.querySelectorAll(".c-focus-inp input")[0]) {
      document.querySelectorAll(".c-focus-inp input")[0].focus();
    }
  }, 500);
}

const dataSource1 = ref([]);
const shoplistfn = () => {
  shoplist()
    .then(async (res) => {
      dataSource1.value = res || [];
      await nextTick();
      treeSelect.value.setCurrentKey(parseInt(searchParams.shop_id));
    })
    .catch((err) => {
      // if (err.response.data && err.response.data.detail == "知识库类目不存在") {
      //   dataSource.value = [];
      // }
    });
};
shoplistfn()
const dataSource = ref([]);
const treeSelect = ref(null);
const treeSelect1 = ref(null);
const checkType = async (item) => {
  initSearchParams();
  if (searchParams.active == 1) {
    searchParams.shop_id = item.id;

  } else {
    searchParams.category_id = item.id;
  }
  search();
  // dataSource.value = [].concat(dataSource.value);
  // dataSource1.value = [].concat(dataSource1.value);


};



const searchCate = (params) => {
  categorieslist()
    .then(async (res) => {
      dataSource.value = res || [];
      await nextTick();
      treeSelect.value.setCurrentKey(parseInt(searchParams.category_id));
    })
    .catch((err) => {
      // if (err.response.data && err.response.data.detail == "知识库类目不存在") {
      //   dataSource.value = [];
      // }
    });
};
searchCate();

const plists = ref([]);
const platformlistfn = () => {
  platformlist().then((res) => {
    plists.value = res;
  });
};
platformlistfn()
const dialogFormVisibletitle = ref("新增分类");
const addTypefn = async (item, type) => {
  if (item.id) {
    if (searchParams.active == 1) {
      dialogFormVisibletitle.value = "编辑店铺";
      addparam.value.pid = item.pid;
      addparam.value.id = item.id;
    } else {
      dialogFormVisibletitle.value = "编辑分类";
      addparam.value.id = item.id;
      addparam.value.platform_id = item.platform_id;
    }
    addparam.value.shop_name = item.name;
    addparam.value.pid = item.pid;
    addparam.value.id = item.id;
    addparam.value.platform_id = item.platform_id;
  } else {
    if (searchParams.active == 1) {
      dialogFormVisibletitle.value = "新增店铺";
    } else {
      dialogFormVisibletitle.value = "新增分类";
    }
    addparam.value = initializeForm(1)
  }

  if (type == "child") {
    // 添加子节点
    addparam.value.pid = item.id;
    addparam.value.shop_name = "";
    addparam.value.platform_id = "";
    addparam.value.id = 0;
  }
  focus();
  dialogFormVisible.value = true;

};

const errfn = (err) => {
  let myError = err.toString();
  myError = myError.replace("UploadAjaxError: ", "");
  myError = JSON.parse(myError);
  _this.$message(myError.detail, "error");
  // 报错也查询一下
  store.commit("loading", false)
  search();
};
const uploadRef = ref(null);
const uploadRef1 = ref(null);
const sucfn = (res, file, files) => {
  _this.$message("导入成功");
  if (uploadRef.value) uploadRef.value.clearFiles();
  if (uploadRef1.value) uploadRef1.value.clearFiles();
  store.commit("loading", false)
  search();
};
const fileList = ref([]);
const beforeAvatarUpload = (file) => {
  if (searchParams.active == 1 && !searchParams.shop_id) {
    _this.$message("请先选择店铺", "error");
    return false;
  }
  store.commit("loading", true)
  return true;
};

const initTz = () => {
  let num = 0;
  form.value.profile_tuple.forEach((item) => {
    num += item.quantity
  })
  if (num > 1) {
    form.value.suite_flag = true
  } else {
    form.value.suite_flag = false
  }
}
const searchheight = ref(0);
const tableRef = ref(null);
const tableRef2 = ref(null);
</script>

<template>
  <div class="pagelistbox">
    <div class="c-titlebox">
      <span class="title">商品管理</span>
      <div class="btns">
        <el-link v-if="searchParams.active == '1'" @click="download('/api/goods/download/goods_template')"> <span
            class="iconfont icon-anniu-xiazai"></span> 下载店铺商品模板</el-link>
        <el-link v-if="searchParams.active == '2'" @click="download('/api/goods/download/profile_template')"> <span
            class="iconfont icon-anniu-xiazai"></span>下载商品档案模板</el-link>

        <el-button v-if="searchParams.active == '1'" @click="addfn()" size="small" type="primary">新增商品</el-button>
        <el-upload v-if="searchParams.active == '1'" class="upload-demo" ref="uploadRef" v-model:file-list="fileList"
          :headers="{ authorization: 'Bearer ' + store.state.token }" :before-upload="beforeAvatarUpload"
          :show-file-list="false" :on-error="errfn" :on-success="sucfn" :data="{ shop_id: searchParams.shop_id }"
          :limit="1" action="/api/goods/import">
          <el-button class="on" style="border: none;" size="small" plain>导入商品</el-button>
        </el-upload>

        <el-button v-if="searchParams.active == '2'" @click="addfn()" size="small" type="primary">新增档案</el-button>
        <el-upload v-if="searchParams.active == '2'" class="upload-demo" ref="uploadRef1" v-model:file-list="fileList"
          :headers="{ authorization: 'Bearer ' + store.state.token }" :before-upload="beforeAvatarUpload"
          :show-file-list="false" :on-error="errfn" :on-success="sucfn" :limit="1" action="/api/goods/profile/import">
          <el-button size="small" plain>导入档案</el-button>
        </el-upload>
      </div>
    </div>

    <div class="tabbox">
      <el-tabs v-model="searchParams.active" class="demo-tabs" @tab-change="handleClick">
        <el-tab-pane name="1">
          <template #label>
            店铺商品
          </template>
        </el-tab-pane>
        <el-tab-pane name="2">
          <template #label>
            商品档案
          </template>
        </el-tab-pane>

      </el-tabs>
    </div>

    <div class="c-tablebox tableboxContain c-tooltip c-bodybox">
      <div class="leftbox">



        <template v-if="searchParams.active == 2">
          <div class="topbtns">
            <span class="title">分类</span>
            <el-button @click="checkType({ id: undefined })" class="on noradius" plain>
              <span class="iconfont icon-anniu-zhankai"></span>
              查看全部
            </el-button>

          </div>

          <div class="contain">
            <el-scrollbar>

              <div class="el-tree el-tree--highlight-current" role="tree" style="width: 100%">
                <div class="el-tree-node" :class="{ 'is-current': searchParams.category_id == 0 }">
                  <div class="el-tree-node__content" style="padding-left: 0px">
                    <div @click="checkType({ id: 0 })" style="padding-left: 35px" class="custom-tree-node">
                      <div class="item">
                        未分类
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <el-tree ref="treeSelect" style="width: 100%" :data="dataSource" node-key="id" empty-text="暂无分类信息"
                highlight-current
                :current-node-key="searchParams.category_id ? parseInt(searchParams.category_id) : undefined"
                default-expand-all @node-click="checkType" :expand-on-click-node="false">
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
            <el-button style="width: 100%;" plain class="on noradius" @click="addTypefn({ name: '', id: 0 })"><span
                class="iconfont icon-liebiao-xinzeng"></span>
              新增分类</el-button>
          </div>
        </template>

        <template v-if="searchParams.active == 1" class="catebox navbox">


          <div class="topbtns">
            <span class="title">店铺</span>
            <el-button @click="checkType({ id: undefined })" class="on noradius" plain>
              <span class="iconfont icon-anniu-zhankai"></span>
              查看全部
            </el-button>

          </div>
          <div class="contain">
            <el-scrollbar>

              <el-tree ref="treeSelect1" style="width: 100%" :data="dataSource1" node-key="id" empty-text="暂无店铺信息"
                highlight-current :current-node-key="searchParams.shop_id ? parseInt(searchParams.shop_id) : undefined"
                default-expand-all @node-click="checkType" :expand-on-click-node="false">
                <template #default="{ node, data }">
                  <div :title="data.name + '(' + data.platform_name + ')'" class="custom-tree-node">
                    <div class="item">
                      <icon type="treedianpu" width="20" height="20"></icon>
                      <p class="ellipsis">{{ data.name + '(' + data.platform_name + ')' }}</p>
                    </div>
                    <div class="btns">
                      <span title="修改" @click.stop="addTypefn(data)" class="iconfont icon-xiugai"></span>
                      <span title="删除店铺" @click.stop="delTypefn(data)" class="iconfont icon-shuzhuang-shanchu"></span>
                    </div>
                  </div>
                </template>
              </el-tree>
            </el-scrollbar>
          </div>

          <div class="botbtns">
            <el-button style="width: 100%;" plain class="on noradius" @click="addTypefn({ name: '', id: 0 })"><span
                class="iconfont icon-liebiao-xinzeng"></span>
              新增店铺</el-button>
          </div>
        </template>
      </div>


      <div v-show="searchParams.active == 1" class="rightbox">
        <div class="c-top-searchbox c-js-item">
          <el-form :model="searchParams" ref="searchFormRef" inline class="demo-form-inline">
            <el-form-item style="width: 240px" label="分类" prop="is_modified">
              <el-tree-select v-model="searchParams.category_id" filterable check-strictly
                :props="{ children: 'children', label: 'name', value: 'id' }" :default-expand-all="true"
                :check-on-click-node="true" :data="dataSource">
                <template #default="{ node, data }">
                  <span>{{ data.name }}</span>
                </template>
              </el-tree-select>

            </el-form-item>
            <el-form-item style="width: calc(20% - 16px);margin-right: 16px;" label="商品SKU" prop="sku">
              <el-input v-model="searchParams.sku" autocomplete="off" />
            </el-form-item>
            <el-form-item style="width: calc(20% - 16px);margin-right: 16px;" label="商品编码" prop="goods_code">
              <el-input v-model="searchParams.goods_code" autocomplete="off" />
            </el-form-item>
            <el-form-item style="width: calc(20% - 16px);margin-right: 16px;" label="套装标记" prop="suite_flag">
              <el-select v-model="searchParams.suite_flag" placeholder="请选择">
                <el-option label="套装" :value="true" />
                <el-option label="无" :value="false" />
              </el-select>
            </el-form-item>
            <el-form-item style="width: calc(20% - 16px);margin-right: 16px;" label="销售状态" prop="on_sale_flag">
              <el-select v-model="searchParams.on_sale_flag" placeholder="请选择">
                <el-option label="上架" :value="true" />
                <el-option label="下架" :value="false" />
              </el-select>
            </el-form-item>
            <el-form-item style="width: calc(20% - 16px);margin-right: 16px;" label="推荐标记" prop="recommend_flag">
              <el-select v-model="searchParams.recommend_flag" placeholder="请选择">
                <el-option label="推荐" :value="true" />
                <el-option label="无" :value="false" />
              </el-select>
            </el-form-item>

            <el-form-item style="width: calc(20% - 16px);margin-right: 16px;" label="是否关联档案" prop="is_empty_profile">
              <el-select v-model="searchParams.is_empty_profile" placeholder="请选择">
                <el-option label="没有关联" :value="true" />
                <el-option label="有关联" :value="false" />
              </el-select>
            </el-form-item>


          </el-form>
          <div class="rbox">
            <span v-searchOpen
              @click="searchheight == 0 ? searchheight = 67 : searchheight = 0; tableRef && tableRef.update()"
              class="c-search-openbtn">
              <span class="iconfont icon-anniu-zhankai"></span><span class="opentext">展开</span><span
                class="closetext">收起</span>
            </span>
            <el-button @click="search('init')" type="primary">查询</el-button>
            <el-button @click="initSearchParams()" plain>重置</el-button>
          </div>
        </div>
        <div class="tablebox">
          <div class="contain">
            <el-table tooltip-effect="light" border :max-height="store.getters.innerHeight - 294 - searchheight"
              :data="pagelist" style="width: 100%" ref="tableRef">
              <!-- <el-table-column prop="id" width="80" label="id" /> -->
              <el-table-column prop="sku" width="140" label="商品SKU" />

              <el-table-column width="100" align="center" label="套装标记">
                <template #default="scope">
                  {{ scope.row.suite_flag ? '套装' : '无' }}
                </template>
              </el-table-column>
              <el-table-column width="100" align="center" label="销售状态">
                <template #default="scope">
                  {{ scope.row.on_sale_flag ? '上架' : '下架' }}
                </template>
              </el-table-column>
              <el-table-column width="100" align="center" label="推荐标记">
                <template #default="scope">
                  {{ scope.row.recommend_flag ? '推荐' : '无' }}
                </template>
              </el-table-column>
              <el-table-column width="160" label="分类">
                <template #default="scope">
                  {{ scope.row.goods_category_name }}
                </template>
              </el-table-column>



              <el-table-column label="关联档案名称">
                <template #default="scope">

                  <el-popover v-if="scope.row.profiles_name" placement="top-start" :width="500" trigger="hover">
                    <template #reference>
                      <div class="ellipsis2">
                        {{ scope.row.profiles_name }}
                      </div>
                    </template>

                    <div style="margin: 0 -20px;">
                      <el-scrollbar max-height="400">
                        <div v-html="scope.row.profiles_name" style="margin:0 20px;">
                        </div>
                      </el-scrollbar>
                    </div>
                  </el-popover>
                </template>
              </el-table-column>
              <el-table-column width="160" label="店铺">
                <template #default="scope">
                  {{ scope.row.shop_name }}
                </template>
              </el-table-column>

              <el-table-column width="160" align="center" label="添加时间">
                <template #default="scope">
                  {{
                    getTime(scope.row.created_at)
                  }}
                </template>
              </el-table-column>
              <el-table-column width="160" align="center" label="修改时间">
                <template #default="scope">
                  {{
                    getTime(scope.row.updated_at)
                  }}
                </template>
              </el-table-column>

              <el-table-column width="160" align="center" label="操作">
                <template #default="scope">

                  <div @click="addfn(scope.row)" class="c-table-ibtn">
                    <span class="iconfont icon-xiugai"></span>
                    修改
                  </div>
                  <div @click="delfn(scope.row)" class="c-table-ibtn c-btn-del">
                    <span class="iconfont icon-shuzhuang-shanchu"></span>
                    删除
                  </div>


                </template>
              </el-table-column>
              <template #empty="scope">
                <div class="c-emptybox">
                  <icon type="empzwssjg" width="100" height="100"></icon>暂无数据~~
                </div>
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
                      tableRef && tableRef.scrollTo(0, 0);
                      search();
                    }
                  " :page-sizes="[30, 50, 100, 900]" layout="total,sizes,jumper,prev, pager, next" :total="total" />
            </div>
          </div>
        </div>
      </div>

      <div v-initTableHeight v-show="searchParams.active == 2" class="rightbox">
        <div class="c-top-searchbox c-js-item">
          <el-form :model="searchParams" ref="searchFormRef1" inline class="demo-form-inline">

            <el-form-item label="商品编码" prop="goods_code">
              <el-input v-model="searchParams.goods_code" autocomplete="off" />
            </el-form-item>

            <el-form-item label="商品条码" prop="barcode">
              <el-input v-model="searchParams.barcode" autocomplete="off" />
            </el-form-item>

            <el-form-item label="商品名称" prop="name">
              <el-input v-model="searchParams.name" autocomplete="off" />
            </el-form-item>


          </el-form>
          <div class="rbox">

            <el-button @click="search('init')" type="primary">查询</el-button>
            <el-button @click="initSearchParams()" plain>重置</el-button>


          </div>
        </div>
        <div class="tablebox c-js-body">
          <div class="contain">
            <el-table tooltip-effect="light" ref="tableRef2" border :data="pagelist"
              :max-height="store.getters.innerHeight - 294" style="width: 100%">
              <el-table-column prop="id" width="160" label="商品id" />
              <el-table-column width="160" label="商品编码">
                <template #default="scope">
                  <div class="c-scroll-contain">
                    {{ scope.row.goods_code }}
                  </div>
                </template>
              </el-table-column>
              <el-table-column width="160" label="商品条码">
                <template #default="scope">
                  <div class="c-scroll-contain">
                    {{ scope.row.barcode }}
                  </div>
                </template>
              </el-table-column>
              <el-table-column width="160" label="分类">
                <template #default="scope">
                  <div class="c-scroll-contain">
                    {{ scope.row.category_name }}
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="商品名称">
                <template #default="scope">
                  <div class="c-scroll-contain">
                    {{ scope.row.name }}
                  </div>
                </template>
              </el-table-column>


              <el-table-column width="160" align="center" label="添加时间">
                <template #default="scope">
                  {{
                    getTime(scope.row.created_at)
                  }}
                </template>
              </el-table-column>
              <el-table-column width="160" align="center" label="修改时间">
                <template #default="scope">
                  {{
                    getTime(scope.row.updated_at)
                  }}
                </template>
              </el-table-column>

              <el-table-column width="160" align="center" label="操作">
                <template #default="scope">

                  <div @click="addfn(scope.row)" class="c-table-ibtn">
                    <span class="iconfont icon-xiugai"></span>
                    修改
                  </div>
                  <div @click="delfn(scope.row)" class="c-table-ibtn c-btn-del">
                    <span class="iconfont icon-shuzhuang-shanchu"></span>
                    删除
                  </div>

                </template>
              </el-table-column>
              <template #empty="scope">
                <div class="c-emptybox">
                  <icon type="empzwssjg" width="100" height="100"></icon>暂无数据~~
                </div>
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
                      tableRef2 && tableRef2.scrollTo(0, 0);
                      search();
                    }
                  " :page-sizes="[30, 50, 100, 900]" layout="total,sizes,jumper,prev, pager, next" :total="total" />
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>

  <el-drawer v-model="isShowCompDetail" @closed="isShowCompDetail = false"
    :title="(form.id ? '修改' : '新增') + (searchParams.active == 1 ? '店铺商品' : '商品档案')"
    :size="searchParams.active == 1 ? '90%' : '800px'" direction="rtl">
    <div class="dformbox">
      <el-scrollbar>
        <el-form v-if="searchParams.active == 2" @submit.native.prevent inline label-position="top" label-width="auto"
          ref="ruleFormRef" :model="form">
          <el-form-item style="width: calc(50% - 8px);margin-right: 16px;" label="商品id" prop="id">
            <el-input v-model="form.id" disabled autocomplete="off" />
          </el-form-item>
          <el-form-item style="width: calc(50% - 8px);margin-right: 0px;" label="商品编码" prop="goods_code">
            <el-input v-model="form.goods_code" autocomplete="off" />
          </el-form-item>
          <el-form-item style="width: calc(50% - 8px);margin-right: 16px;" label="商品条码" prop="barcode">
            <el-input v-model="form.barcode" autocomplete="off" />
          </el-form-item>
          <el-form-item style="width: calc(50% - 8px);margin-right: 0px;" label="商品类目" prop="category_id">

            <el-tree-select v-model="form.category_id" filterable check-strictly
              :props="{ children: 'children', label: 'name', value: 'id' }" :default-expand-all="true"
              :check-on-click-node="true" :data="dataSource" style="width: 100%">
              <template #default="{ node, data }">
                <span>{{ data.name }}</span>
              </template>
            </el-tree-select>


          </el-form-item>


          <el-form-item style="width:100%;margin-right: 0;" :rules="[
            {
              required: true,
              message: '请输入商品名称',
              trigger: 'blur',
            },
          ]" label="商品名称" prop="goods_name">
            <el-input v-model="form.goods_name" type="textarea" autocomplete="off" />
          </el-form-item>
        </el-form>



        <el-form v-if="searchParams.active == 1" @submit.native.prevent inline label-position="top" label-width="auto"
          ref="ruleFormRef" :model="form">
          <el-form-item style="width: calc(20% - 16px);margin-right: 16px;" label="商品SKU" :rules="[
            {
              required: true,
              message: '请输入商品SKU',
              trigger: 'blur',
            },
          ]" prop="sku">
            <el-input v-model="form.sku" autocomplete="off" />
          </el-form-item>
          <el-form-item style="width: calc(20% - 16px);margin-right: 16px;" label="店铺" prop="shop_id">
            <el-select v-model="form.shop_id" placeholder="">
              <el-option v-for="item in dataSource1" :label="item.name" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item style="width: calc(20% - 16px);margin-right: 16px;" label="商品类目" prop="category_id">
            <el-tree-select v-model="form.category_id" filterable check-strictly
              :props="{ children: 'children', label: 'name', value: 'id' }" :default-expand-all="true"
              :check-on-click-node="true" :data="dataSource" style="width: 100%">
              <template #default="{ node, data }">
                <span>{{ data.name }}</span>
              </template>
            </el-tree-select>

          </el-form-item>

          <el-form-item class="c-switchbox-label" style="width: calc(13.33% - 11px);margin-right: 16px;" label="套装标记" prop="suite_flag">

            <div disabled class="c-switchbox">
              <div class="label"></div>
              <div class="switch">
                <el-switch disabled v-model="form.suite_flag" inline-prompt active-text="套装" inactive-text="无" />
              </div>
            </div>
          </el-form-item>

          <el-form-item class="c-switchbox-label" style="width: calc(13.33% - 11px);margin-right: 16px;" label="销售状态" prop="on_sale_flag">

            <div class="c-switchbox">
              <div class="label"></div>
              <div class="switch">
                <el-switch v-model="form.on_sale_flag" inline-prompt active-text="上架" inactive-text="下架" />
              </div>
            </div>

          </el-form-item>

          <el-form-item class="c-switchbox-label" style="width: calc(13.34% - 10px);margin-right: 0px;" label="推荐标记" prop="recommend_flag">


            <div class="c-switchbox">
              <div class="label"></div>
              <div class="switch">
                <el-switch v-model="form.recommend_flag" inline-prompt active-text="推荐" inactive-text="无" />
              </div>
            </div>
          </el-form-item>
          <br>

          <el-form-item style="width: calc(20% - 16px);margin-right: 16px;" label="零售价" prop="price">
            <el-input-number style="width: 100%;" @focus="$event.target.select();" :controls="false" :min="0"
              :precision="2" placeholder="请输入零售价" v-model="form.price"></el-input-number>
          </el-form-item>

          <br>

          <el-form-item style="width:calc(80%);margin-right: 0px;" label="商品卖点" prop="sale_point">
            <el-input v-model="form.sale_point" type="input" autocomplete="off" />
          </el-form-item>



          <div class="ltitlebox">
            <div class="ltitle">关联档案</div>
            <div class="inp" style="position: relative;">
              <el-input v-model="curprofile_code" style="width:100%;" placeholder="商品编码，条码" autocomplete="off" />
              <el-button style="position: absolute;right: 0;top: 0;border-radius: 8px;" @click="searchAddlist()"
                type="primary">新增</el-button>
            </div>

          </div>

          <div class="c-tablebox">
            <el-table tooltip-effect="light" border :data="form.profile_tuple" style="width: 100%">
              <el-table-column width="120" label="商品id">
                <template #default="scope">
                  {{ scope.row.id }}
                </template>
              </el-table-column>
              <el-table-column width="120" label="商品编码">
                <template #default="scope">
                  {{ scope.row.goods_code }}
                </template>
              </el-table-column>
              <el-table-column width="120" label="商品条码">
                <template #default="scope">
                  {{ scope.row.barcode }}
                </template>
              </el-table-column>

              <el-table-column width="220" label="配置数量">
                <template #default="scope">

                  <el-input-number @change="initTz" :controls="false" :min="1" :precision="0" placeholder=""
                    v-model="scope.row.quantity"></el-input-number>
                </template>
              </el-table-column>

              <el-table-column label="商品名称">
                <template #default="scope">
                  {{ scope.row.name }}
                </template>
              </el-table-column>

              <el-table-column width="120" label="操作">
                <template #default="scope">
                  <el-form-item>

                    <div @click="form.profile_tuple.splice(scope.$index, 1); initTz()" class="c-table-ibtn c-btn-del">
                      <span class="iconfont icon-shuzhuang-shanchu"></span>
                      删除
                    </div>
                  </el-form-item>
                </template>
              </el-table-column>


            </el-table>
          </div>



        </el-form>
      </el-scrollbar>
    </div>
    <div class="dialog-footer">

      <el-button type="primary" @click="sub(ruleFormRef)">
        保存
      </el-button>

      <el-button plain @click="isShowCompDetail = false">
        取消
      </el-button>
    </div>

  </el-drawer>


  <el-dialog align-center v-model="dialogFormVisible" :title="dialogFormVisibletitle" width="600">
    <el-form @submit.native.prevent :model="addparam" label-width="100" @keyup.native.enter="addshop(addFormRef)"
      ref="addFormRef">
      <el-form-item label="名称" :rules="[
        {
          required: true,
          message: '请输入名称',
          trigger: 'blur',
        },
      ]" prop="shop_name">
        <el-input class="c-focus-inp" v-model="addparam.shop_name" autocomplete="off" />
      </el-form-item>

      <el-form-item v-if="searchParams.active == 1" label="平台" :rules="[
        {
          required: true,
          message: '请选择平台',
          trigger: 'change',
        },
      ]" prop="platform_id">
        <el-select v-model="addparam.platform_id" placeholder="">
          <el-option v-for="item in plists" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>

    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogFormVisible = false">取消</el-button>
        <el-button type="primary" @click="addshop(addFormRef)">
          确定提交
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>
<style scoped>
.c-top-searchbox {
  margin-left: 24px;
  margin-right: 24px;
}

.upload-demo {
  margin-left: 12px;
}



.ltitlebox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 10px;
  width: 100%;
}

.ltitlebox .ltitle {
  font-weight: bold;
  text-align: left;
  font-size: 12px;
}

.dialog-footer {
  text-align: center;
  padding-top: 10px;
}

.dtitle {
  padding: 0 0 30px 0px;
}

.dtitle .iconfont,
.dtitle {
  font-weight: bold;
  text-align: left;
  font-size: 26px;

}

.dtitle .iconfont {
  cursor: pointer;
}

.dformbox {
  display: block;
  height: calc(100% - 66px);
  text-align: left;
}

.flex {
  display: flex;
  align-items: center;
}







.catebox {
  padding: 0 18px;
  height: calc(100% - 160px);
}

.catebox .treebox {
  border-radius: 5px;
  height: calc(100% - 50px);
}

.catebox .addbtn {
  padding-right: 5px;
}






.catebox .title {
  text-align: left;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tablebox .title {
  padding: 10px;
}

.catebox .btns {
  padding-right: 5px;
}

.catebox .tip {
  font-size: 12px;
  color: #ccc;
}


.searchbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  padding: 0 0px;
  box-sizing: border-box;
  text-align: left;
  width: calc(100% - 10px);
  margin-bottom: 0px;
}

.searchbox .rbox {
  flex-shrink: 0;
}





.icon-shangpin {
  font-size: 28px;
  font-weight: bold;
  color: #1948e7;
}

.topbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-right: 20px;
}


.tableboxContain {
  height: calc(100% - 54px);
}

.tableboxContain .btnbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start
}



.tableboxContain .navtitle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  font-weight: bold;
  font-size: 16px;
}

.tableboxContain .navbox {
  height: calc(100% - 42px);
  text-align: left;
}






.pagelistbox {
  display: block;
  padding: 0;
  width: 100%;
  box-sizing: border-box;
  height: 100%;
}
</style>
