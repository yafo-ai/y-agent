<script setup>
import { ref, reactive, watch } from "vue";
import {
  userpaged,
  rolepaged,
  roledelete,
  roleauthorize_menu,
  roleadd,
  userdelete,
  useradd,
  user,
  userreset_password,
  menutree,
  menurefresh,
  menudelete,
} from "@/api/api";

import { copyData } from "@/assets/utils/util";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";
import { cloneDeep } from "lodash"; // 引入lodash库的cloneDeep方法进行深拷贝
import icon from "@/components/icon.vue";
import Search from "@/components/Search.vue";



const route = useRoute();
const router = useRouter();
const store = useStore();

const delTypefn = (item) => {
  _this.$confirm("确定要删除所选数据?").then((res) => {
    menudelete({ id: item.id }).then((res) => {
      _this.$message("删除成功");
      search();
    });
  });
};

const isShowMenu = ref(false);
const menutreelist = ref([]);
const checkmenu = ref([]);

const curdata = ref({});
const addmenufn = async (item) => {
  curdata.value = item;
  let ids = [];
  item.menus.forEach((citem) => {
    ids.push(citem.id);
  });
  checkmenu.value = ids;

  getmenutree(() => {
    isShowMenu.value = true;
    initCheckList(ids)
    if (treecheckmenu.value) {
      treecheckmenu.value.setCheckedKeys(ids);

    }
  });
};
let sourceData = [];
const menupagelist = ref([]);
const getmenutree = async (fn) => {
  // 没有回调函数 
  if (!(menutreelist.value && menutreelist.value.length > 0) || !fn) {
    let res = await menutree();
    let arr = res || [];
    menutreelist.value = arr;
    menupagelist.value = arr;
    sourceData = arr;
    fn && fn();
  } else {
    menupagelist.value = [...sourceData];

    fn && fn();
  }
};

const treecheckmenu = ref(null);


const refresh = () => {
  menurefresh().then((res) => {
    _this.$message("刷新成功");
    getmenutree();
  });
};
const submenu = () => {
  let arr = []
  if (treecheckmenu.value) {
    arr = treecheckmenu.value.getCheckedKeys();
  }


  roleauthorize_menu({ id: curdata.value.id, menu_ids: arr }).then(
    (res) => {
      _this.$message("授权成功", "success");
      isShowMenu.value = false;
      search();
    }
  );
};

const initSearchParams = () => {
  if (searchParams.active == 1) {
    searchParams.username = "";
    searchParams.nickname = "";

    searchParams.email = "";
    searchParams.phone = "";
    searchParams.is_active = undefined;
    searchParams.is_superuser = undefined;
  } else {
    searchParams.name = "";
  }

  searchParams.page_index = 1;
};

let searchParams = reactive({
  page_index: 1,
  pagesize: 30,
  active: "1",
  name: "",
  username: "",
  nickname: "",

  email: "",
  phone: "",
  is_active: undefined,
  is_superuser: undefined,
});
const total = ref(0);

copyData(searchParams, route.query);

let pagelist = ref([]);

const search = async (type) => {
  if (type == "init") {
    pagelist.value = [];
    searchParams.page_index = 1;
  }

  if (searchParams.active == 1) {
    let params = cloneDeep(searchParams);
    delete params.name;
    delete params.active;
    userpaged(params).then((res) => {
      let arr = res.rows || [];

      pagelist.value = arr;
      total.value = res.total;
    });
  } else if (searchParams.active == 2) {
    rolepagedfn({ name: searchParams.name }, (arr) => {
      pagelist.value = arr;
    });
  } else if (searchParams.active == 3) {
    getmenutree();
  }

  if (type != "noquery") {
    let query = { ...route.query, ...searchParams };
    router.replace({ path: route.path, query: query });
  }
};
const rolepagedfn = (params, fn) => {
  rolepaged(params).then((res) => {
    let arr = res.rows || [];
    roles.value = arr;
    fn && fn(arr);
    total.value = res.total;
  });
};

search("noquery");

if (searchParams.active == 1) {
  rolepagedfn({ name: "" });
}

const scrollbarRef = ref(null);

const delfn = (item) => {
  _this.$confirm("确定要删除所选数据?").then((res) => {
    if (searchParams.active == 1) {
      userdelete({ id: item.id }).then((res) => {
        _this.$message("删除成功");

        search();
      });
    } else if (searchParams.active == 2) {
      roledelete({ id: item.id }).then((res) => {
        _this.$message("删除成功");

        search();
      });
    }
  });
};
const isShowCompDetail = ref(false);

const initializeForm = () => {
  if (searchParams.active == 1) {
    return {
      username: "",
      password: "",
      nickname: "",
      email: "",
      phone: "",
      is_active: true,
      is_superuser: false,
      role_ids: [],
    };
  } else if (searchParams.active == 2) {
    return { name: "" };
  }
};

const roles = ref([]);
const isShowCompDetailTitle = ref("新增");
const form = ref(initializeForm());
const addfn = async (item) => {
  if (item) {

    if (searchParams.active == 1) {
      let res = await user({ id: item.id });
      let arr = [];
      res.roles.forEach((element) => {
        arr.push(element.id);
      });
      res.role_ids = arr;
      isShowCompDetailTitle.value = "修改用户";
      form.value = res;
    } else {
      isShowCompDetailTitle.value = "修改角色";
      form.value = item;
    }
  } else {

    if (searchParams.active == 1) {
      isShowCompDetailTitle.value = "新增用户";
    } else {
      isShowCompDetailTitle.value = "新增角色";
    }
    form.value = initializeForm();
  }
  isShowCompDetail.value = true;

  if (ruleFormRef.value) {
    ruleFormRef.value.clearValidate();
  }
};
const ruleFormRef = ref(null);
const sub = (formEl) => {
  if (!formEl) return;
  formEl.validate((valid) => {
    if (valid) {
      if (searchParams.active == 1) {
        let params = cloneDeep(form.value);
        delete params.name;
        useradd(params).then((res) => {
          _this.$message("保存成功");
          search();
          isShowCompDetail.value = false;
        });
      } else if (searchParams.active == 2) {
        roleadd({ id: form.value.id, name: form.value.name }).then((res) => {
          _this.$message("保存成功");
          search();
          isShowCompDetail.value = false;
        });
      }
    }
  });
};

const handleClick = (tab, event) => {
  total.value = 0;
  initSearchParams();
  search("init");
};

const filterMethod = (value) => {
  if (!value) {
    menutreelist.value = [...sourceData];
    return true;
  }
  menutreelist.value = [...sourceData].filter(
    (item) => !item.name || item.name.includes(value)
  );
};
const passwordformref = ref(null);
const isShowPsd = ref(false);
const passwordform = reactive({
  id: "",
  old_password: "",
  new_password: "",
});
const showpwd = (item) => {
  passwordform.id = item.id;
  passwordform.old_password = "";
  passwordform.new_password = "";
  isShowPsd.value = true;
};
const subpwd = (formEl) => {
  if (!formEl) return;
  formEl.validate((valid) => {
    if (valid) {
      userreset_password(passwordform).then((res) => {
        isShowPsd.value = false;
        _this.$message("重置密码成功");
        search();
      });
    }
  });
};

const searchList = ref([
  { label: '用户名', prop: 'username', type: 'input', clearable: true, value: '', valType: 'string', check: true },
  { label: '昵称', prop: 'nickname', type: 'input', clearable: true, value: '', valType: 'string', check: true },
  { label: '邮箱', prop: 'email', type: 'input', clearable: true, value: '', valType: 'string', check: true },
  { label: '手机号', prop: 'phone', type: 'input', clearable: true, value: '', valType: 'string', check: true },
])

let timer = null;
const checkcfn = (data, data1, d3) => {
  clearTimeout(timer)
  timer = setTimeout(() => {
    let arr = []
    if (treecheckmenu.value) {
      arr = treecheckmenu.value.getCheckedKeys();
    }
    initCheckList(arr)
  }, 70)
}

const curCheckList = ref([])
const curCheckIds = ref([])

const initCheckList = (ids = []) => {
  if (!Array.isArray(ids) || !menutreelist.value) return;
  curCheckIds.value = ids;
  const arr = cloneDeep(menutreelist.value);

  const processNode = (node) => {
    const isChecked = ids.includes(node.id);
    node.checked = isChecked;
    node.isshow = isChecked;

    if (node.children?.length) {
      let hasCheckedChild = false;
      node.children.forEach(child => {
        processNode(child);
        if (child.checked) hasCheckedChild = true;
      });

      if (!isChecked) {
        node.isshow = hasCheckedChild;
      }
    }
  };

  arr.forEach(processNode);
  curCheckList.value = arr;
};

const filterText = ref('')
watch(filterText, (val) => {
  treecheckmenu.value?.filter(val)
})

const filterNode = (value, data) => {
  if (!value) return true
  return data.name.includes(value)
}
</script>

<template>
  <div class="pagelistbox">
    <div class="c-titlebox">
      <span class="title">用户管理</span>
    </div>
    <div style="margin-bottom: -15px;" class="tabbox">
      <el-tabs v-model="searchParams.active" class="demo-tabs" @tab-change="handleClick">
        <el-tab-pane name="1">
          <template #label> 用户管理 </template>
        </el-tab-pane>
        <el-tab-pane name="2">
          <template #label> 角色管理 </template>
        </el-tab-pane>
        <el-tab-pane name="3">
          <template #label> 菜单管理 </template>
        </el-tab-pane>
      </el-tabs>
    </div>

    <div v-if="searchParams.active == 3" class="refreshbox"><el-button style="position: relative; top: -40px;"
        @click="refresh()" type="primary">刷新</el-button></div>



    <div v-if="searchParams.active != 3" class="searchbox">
      <el-form :model="searchParams" ref="searchFormRef" inline class="demo-form-inline">
        <template v-if="searchParams.active == 1">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="searchParams.username" autocomplete="off" />
          </el-form-item>
          <el-form-item label="昵称" prop="nickname">
            <el-input v-model="searchParams.nickname" autocomplete="off" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="searchParams.email" autocomplete="off" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="searchParams.phone" autocomplete="off" />
          </el-form-item>
        </template>
        <el-form-item v-if="searchParams.active == 2" label="名称" prop="phone">
          <el-input v-model="searchParams.name" autocomplete="off" />
        </el-form-item>
      </el-form>
      <div class="rbox">
        <div class="el-form-item asterisk-left">
          <!--v-if-->
          <div v-if="searchParams.active != 3" class="el-form-item__content">
            <el-button @click="search('init')" type="primary">查询</el-button>
            <el-button @click="initSearchParams()">重置</el-button>
            <el-button @click="addfn()">{{
              searchParams.active == 1 ? "新增用户" : "新增角色"
            }}</el-button>
          </div>


        </div>
      </div>
    </div>




    <div class="c-tablebox tableboxContain c-tooltip" :class="{ active3: searchParams.active == 3 }">
      <div class="bodybox">

        <el-table ref="tableRef" tooltip-effect="light" :max-height="store.getters.innerHeight - 252"
          v-if="searchParams.active == 1" border :data="pagelist" style="width: 100%">
          <el-table-column prop="id" width="70" label="用户id" />

          <el-table-column width="160" label="账号">
            <template #default="scope">
              <div class="c-scroll-contain">
                {{ scope.row.username }}
              </div>
            </template>
          </el-table-column>


          <el-table-column label="用户角色">
            <template #default="scope">
              <div class="c-scroll-contain rolesbox">
                <span class="c-plain-btn" v-for="item in scope.row.roles">{{ item.name }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column width="200" label="昵称">
            <template #default="scope">
              <div class="c-scroll-contain">
                {{ scope.row.nickname }}
              </div>
            </template>
          </el-table-column>

          <el-table-column width="200" label="邮箱">
            <template #default="scope">
              <div class="c-scroll-contain">
                {{ scope.row.email }}
              </div>
            </template>
          </el-table-column>

          <el-table-column width="140" align="center" label="电话">
            <template #default="scope">
              <div class="c-scroll-contain">
                {{ scope.row.phone }}
              </div>
            </template>
          </el-table-column>

          <el-table-column width="120" align="center" label="是否启用">
            <template #default="scope">
              {{ scope.row.is_active ? "启用" : "禁用" }}
            </template>
          </el-table-column>
          <el-table-column width="120" align="center" label="是否管理员">
            <template #default="scope">
              {{ scope.row.is_superuser ? "是" : "否" }}
            </template>
          </el-table-column>

          <el-table-column width="260" align="center" label="操作">
            <template #default="scope">
              <!-- <el-button @click="showpwd(scope.row)" type="primary" size="small">重置密码</el-button> -->

              <div @click="showpwd(scope.row)" class="c-table-ibtn">
                <span class="iconfont icon-liebiao-mima"></span>
                重置密码
              </div>
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

        <el-scrollbar v-if="searchParams.active == 2" ref="tableRef" :max-height="store.getters.innerHeight - 252">
          <div class="c-cardbox">
            <div v-for="ritem in pagelist"  class="item">
              <el-popover :width="160">
                <template #reference>
                  <span class="iconfont icon-gengduo c-cardbtn-icon"></span>
                </template>
                <template #default>
                  <div class="c-cardbtn-btns">

                    <div @click.stop="addmenufn(ritem)" class="item">
                      <span class="name">菜单授权</span>
                    </div>
                    <div @click.stop="addfn(ritem)" class="item">
                      <span class="name">修改</span>
                    </div>
                    <div @click.stop="delfn(ritem)" class="item">
                      <span class="name">删除</span>
                    </div>
                  </div>
                </template>
              </el-popover>
              <div class="top ellipsis">
                # {{ ritem.id }}
              </div>
              <div class="title ellipsis">
                {{ ritem.name }}
              </div>
              <div class="intro ellipsis3">
                <el-popover v-if="ritem.menus && ritem.menus.length > 0" placement="top-start" :width="380"
                  trigger="hover">
                  <template #reference>
                    <div class="ellipsis3">
                      <span v-for="item in ritem.menus">{{ item.name }},</span>
                    </div>
                  </template>

                  <div style="margin: 0 -20px;">
                    <el-scrollbar max-height="400">
                      <div class="ellipsis flex" style="padding-bottom: 10px;display: flex;align-items: center;margin: 0 20px;"
                        :title="item.name" v-for="item in ritem.menus">

                        <icon :title="item.type_name" v-if="item.type != 2" type="mulu"></icon>
                        <icon :title="item.type_name" v-else type="btn"></icon>
                        <span style="margin-left: 5px;">{{ item.name }} </span>

                      </div>
                    </el-scrollbar>
                  </div>


                </el-popover>
              </div>
            </div>
          </div>
        </el-scrollbar>
        <div v-if="searchParams.active == 3" style="margin-top: -10px;border-radius: 24px;overflow: hidden;">
          <el-scrollbar ref="tableRef" :max-height="store.getters.innerHeight - 149">
            <div class="c-treebox">
              <el-tree ref="treeSelect" :data="menupagelist" node-key="id" empty-text="暂无菜单信息" highlight-current
                default-expand-all :expand-on-click-node="true">
                <template #default="{ node, data }">
                  <div :title="data.name" class="custom-tree-node">
                    <div class="item">
                      <icon :title="data.type_name" v-if="data.type != 2" type="mulu"></icon>
                      <icon :title="data.type_name" v-else type="btn"></icon>

                      <p class="ellipsis">{{ data.name }}<span v-if="data.api">（{{ data.api }} ）</span></p>
                    </div>
                    <div class="btns">
                      <span title="删除" @click.stop="delTypefn(data)" class="iconfont icon-liebiao-shanchu"></span>
                    </div>
                  </div>
                </template>
              </el-tree>
            </div>
          </el-scrollbar>
        </div>
        <div v-if="total > 0" class="c-pagination">
          <el-pagination :hide-on-single-page="false" background :page-size="searchParams.pagesize"
            :current-page="searchParams.page_index" @size-change="
              (val) => {
                searchParams.pagesize = val;
                searchParams.page_index = Math.min(
                  Math.ceil(total / searchParams.pagesize),
                  searchParams.page_index
                );

                search();
              }
            " @current-change="
                (val) => {
                  searchParams.page_index = val;
                  tableRef && tableRef.scollTo(0, 0);
                  search();
                }
              " :page-sizes="[30, 50, 100, 900]" layout="total,sizes,jumper,prev, pager, next" :total="total" />
        </div>
      </div>
    </div>
  </div>

  <el-drawer v-model="isShowCompDetail" @closed="isShowCompDetail = false" size="1000" :title="isShowCompDetailTitle"
    direction="rtl">

    <div class="dformbox">
      <el-scrollbar>
        <el-form @submit.native.prevent ref="ruleFormRef" label-position="top" inline label-width="auto" :model="form">
          <template v-if="searchParams.active == 1">
            <el-form-item style="width:calc(50% - 8px);" label="账号" :rules="[
              {
                required: true,
                message: '请输入用户名',
                trigger: 'blur',
              },
            ]" prop="username">
              <el-input :disabled="form.id" v-model="form.username" autocomplete="off" />
            </el-form-item>
            <el-form-item v-if="!form.id" style="width:calc(50% - 8px);" label="密码" :rules="[
              {
                required: true,
                message: '请输入密码',
                trigger: 'blur',
              },
            ]" prop="password">
              <el-input  v-model="form.password" autocomplete="off" />
            </el-form-item>

            <el-form-item v-if="form.id" style="width:calc(50% - 8px);" label="密码">
              <el-input disabled autocomplete="off" />
            </el-form-item>

            <el-form-item style="width:calc(50% - 8px);" label="昵称" prop="nickname">
              <el-input v-model="form.nickname" autocomplete="off" />
            </el-form-item>

            <el-form-item style="width:calc(50% - 8px);" label="邮箱" :rules="[
              {
                type: 'email',
                message: '请输入有效的邮箱地址',
                trigger: ['blur'],
              },
            ]" prop="email">
              <el-input v-model="form.email" placeholder="" />
            </el-form-item>

            <el-form-item style="width:calc(50% - 8px);" label="手机号" :rules="[
              {
                pattern: /^1[0123456789]\d{9}$/,
                message: '请输入有效的手机号码',
                trigger: ['blur'],
              },
            ]" prop="phone">
              <el-input v-model="form.phone" placeholder="" />
            </el-form-item>

            <el-form-item style="width:calc(50% - 8px);margin-right: 0;" label="用户角色" prop="role_ids">
              <el-select v-model="form.role_ids" multiple placeholder="">
                <el-option v-for="item in roles" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </el-form-item>

            <el-form-item class="c-switchbox-label" style="width:calc(50% - 8px);margin-top: -26px;" label="是否启用" prop="is_active">

              <div class="c-switchbox">
                <div class="label"></div>
                <div class="switch">
                  <el-switch size="small" v-model="form.is_active" inline-prompt active-text="启用" inactive-text="禁用" />
                </div>
              </div>
            </el-form-item>

            <el-form-item class="c-switchbox-label" style="width:calc(50% - 8px);margin-right: 0;margin-top: -26px;" label="是否管理员" prop="is_superuser">

              <div class="c-switchbox">
                <div class="label"></div>
                <div class="switch">
                  <el-switch size="small" v-model="form.is_superuser" inline-prompt active-text="是" inactive-text="否" />
                </div>
              </div>
            </el-form-item>

            
          </template>

          <el-form-item style="width:calc(50% - 8px);" label="角色名" v-if="searchParams.active == 2" :rules="[
            {
              required: true,
              message: '请输入角色名',
              trigger: 'blur',
            },
          ]" prop="name">
            <el-input style="width: 90%" v-model="form.name" autocomplete="off" />
          </el-form-item>
        </el-form>
      </el-scrollbar>
    </div>
    <div class="dialog-footer">
      <el-button type="primary" @click="sub(ruleFormRef)"> 保存 </el-button>

      <el-button plain @click="isShowCompDetail = false"> 取消 </el-button>
    </div>
  </el-drawer>

  <el-drawer v-model="isShowMenu" @closed="isShowMenu = false" title="菜单授权" size="800" direction="rtl">

    <div class="topbox">



      <div class="totalbox">
        <span class="num">已选择：{{ curCheckIds.length }}</span>
        <span @click="treecheckmenu.setCheckedKeys([])" class="c-btn-text">清空选择</span>
      </div>

      <div style="height: 120px;" class="checklistbox">
        <el-scrollbar>
          <div v-for="item in curCheckList.filter((item) => item.isshow)" :key="item.id" class="item">
            <div class="citem">
              <div class="pname">{{ item.name }} <span v-if="item.api">（{{ item.api }}）</span> </div>
              <span v-if="item.checked && item.isshow" @click="treecheckmenu.setChecked(item.id, false, true)"
                class="iconfont icon-guanbi"></span>
            </div>
            <div v-if="item.children" class="citem" v-for="(citem) in item.children.filter((item) => item.isshow)"
              :key="citem.id">
              <div class="name">{{ citem.name }}<span v-if="citem.api">（{{ citem.api }}）</span></div>
              <span @click="treecheckmenu.setChecked(citem.id, false, true)" class="iconfont icon-guanbi"></span>
            </div>
          </div>
        </el-scrollbar>
      </div>

    </div>

    <div class="row" style="margin: 16px -20px;height: 10px;background: #F6F6F6;"></div>

    <div class="c-treeinpbox">
      <span class="iconfont icon-sousuo1"></span>
      <input v-model="filterText" type="text" placeholder="搜索菜单名称">
    </div>

    <div style="height: calc(100% - 300px);margin:0 -20px" class="dformbox">
      <el-scrollbar>
        <el-tree ref="treecheckmenu" :data="menutreelist" default-expand-all node-key="id"
          :filter-node-method="filterNode" :default-checked-keys="checkmenu"
          :props="{ children: 'children', label: 'name', value: 'id' }" multiple @check-change="checkcfn" show-checkbox
          style="width: 100%">
          <template #default="{ node, data }">
            <div :title="data.name" class="custom-tree-node">
              <div class="item">
                <icon :title="data.type_name" v-if="data.type != 2" type="mulu"></icon>
                <icon :title="data.type_name" v-else type="btn"></icon>

                <p class="ellipsis">{{ data.name }}<span v-if="data.api">（{{ data.api }} ）</span></p>
              </div>

            </div>
          </template>
        </el-tree>
      </el-scrollbar>
    </div>

    <div class="dialog-footer">
      <el-button type="primary" @click="submenu()"> 保存 </el-button>

      <el-button plain @click="isShowMenu = false"> 取消 </el-button>
    </div>
  </el-drawer>

  <el-drawer v-model="isShowPsd" @closed="isShowPsd = false" title="重置密码" size="800" direction="rtl">

    <div class="dformbox">
      <el-form @submit.native.prevent ref="passwordformref" label-position="top" label-width="auto"
        :model="passwordform">
        <el-form-item label="原密码" :rules="[
          {
            required: true,
            message: '请输入原密码',
            trigger: 'blur',
          },
        ]" prop="old_password">
          <el-input v-model="passwordform.old_password" autocomplete="off" />
        </el-form-item>
        <el-form-item label="新密码" :rules="[
          {
            required: true,
            message: '请输入新密码',
            trigger: 'blur',
          },
        ]" prop="new_password">
          <el-input v-model="passwordform.new_password" autocomplete="off" />
        </el-form-item>
      </el-form>
    </div>

    <div class="dialog-footer">
      <el-button type="primary" @click="subpwd(passwordformref)">
        保存
      </el-button>

      <el-button plain @click="isShowPsd = false"> 取消 </el-button>
    </div>
  </el-drawer>
</template>

<style scoped>
.rolesbox .c-plain-btn {
  margin: 5px;
}

.topbox .totalbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  font-weight: 400;
  font-size: 16px;
  color: #999999;
  line-height: 22px;
  text-align: left;
  font-style: normal;
}

.topbox .checklistbox {
  margin-right: -10px;
}

.topbox .checklistbox .citem {
  display: flex;
  padding: 5px 0;
  align-items: center;
  justify-content: space-between;
  font-weight: 400;
  font-size: 14px;
  color: #333333;
  text-align: left;
  font-style: normal;
}

.topbox .checklistbox .citem .iconfont {
  cursor: pointer;
  position: relative;
  left: -10px;
}

.topbox .checklistbox .citem .iconfont:hover {
  color: var(--el-color-primary);
}

.topbox .checklistbox .citem .pname {
  color: var(--el-text-color-regular);
  font-size: 12px;
}

.refreshbox {
  text-align: right;
}

.type_name {
  background: var(--el-color-success);
  margin-right: 3px;
  padding: 2px 5px;
  border-radius: 5px;
  font-size: 12px;
  color: #fff;
}

.type_name.on {
  background: var(--el-color-primary-light-3);
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
  height: calc(100% - 70px);
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




.searchbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 0 0 0;
  box-sizing: border-box;
  text-align: left;
  width: 100%;
  margin-bottom: 0px;
}

.searchbox .rbox {
  padding-top: 4px;
  flex-shrink: 0;
}



.icon-duoren {
  font-size: 28px;
  font-weight: bold;
  color: #1948e7;
}

.topbox {
  display: block;
}


.tableboxContain {
  width: 100%;
  height: auto;
  box-sizing: border-box;
}



.tableboxContain .btnbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
}

.tableboxContain .bodybox {
  height: calc(100% - 0px);
}

.pagelistbox {
  display: block;
  padding: 0;
  width: 100%;
  box-sizing: border-box;
  height: 100%;
}
</style>
