<script setup>
import {
  ref,
} from "vue";
import { useRoute, useRouter, onBeforeRouteLeave } from "vue-router";
import { useStore } from "vuex";
import { documentsGet, productsGet,databaseDetail } from "@/api/api";
import { goback } from "@/components/comp.js";
const route = useRoute();
const router = useRouter();



const mkData = ref("");

const isShop = ref(false);
const shopDetail = ref(null);
const knowledgebase_name = ref("");
const curDetail = ref(null);
const isEdit = ref(false);
if (route.query.type == "product_model") {
  isEdit.value = false;
  productsGet({ id: route.query.did }).then((res) => {
    curDetail.value = res.product;
    if (res.parent_attrs) {
      res.parent_attrs.forEach((item) => {
        item.disabled = true;
      });
      res.product.attrs = res.parent_attrs.concat(res.product.attrs);
    }
    shopDetail.value = res.product;
    document.title = res.product.name;
  });
  isShop.value = true;
  // 商品详情
} else if(route.query.type == "excel_document"){
  isEdit.value = false;
// EXCEL文档
  databaseDetail({id:route.query.rid,code:route.query.did}).then((res)=>{
    isShop.value = false;
    curDetail.value = res;
    mkData.value = res.content
  })
} else {
  isEdit.value = true;
  // 文本详情
  isShop.value = false;
  documentsGet({ id: route.query.did }).then((res) => {
    knowledgebase_name.value = res.knowledgebase_name;
    curDetail.value = res;
    if (res.is_markdown) {
      mkData.value = res.markdown_content;
    } else {
      mkData.value = res.content;
    }
  });
}
</script>

<template>
    <div class="c-titlebox">
      <span @click="goback(null, $router, route.query.fpath || '/dataset/list')" class="title">
        <span class="c-pointer c-flex-center" style="font-size: 14px;">
          <span class="iconfont icon-fuwenben-chexiao"></span>返回列表</span>
      </span>
     <div class="btns">
      <el-button v-if="isEdit" @click="$router.push('/dataset/detail?it=2&id='+route.query.id+'&did='+route.query.did)" size="small" type="primary">前往编辑</el-button>
     </div>
     
    </div>

  <div v-if="curDetail && route.query.type != 'excel_document'" class="breadcrumbbox c-detail-breadcrumbbox">
        <span>{{
          route.query.type == "product_model" ? "产品知识库" : "文档知识库"
        }}</span>
        &nbsp; / &nbsp;
        <el-link
          style="font-size: 16px;color: #909BA5;"
          @click="
            $router.push(
              route.query.type == 'product_model'
                ? '/dataset/shop?id=' +
                    curDetail.knowledgebase_id +
                    '&curid=' +
                    curDetail.id
                : '/dataset/detail?id=' + curDetail.knowledgebase_id
            )
          "
        >
          {{ curDetail.knowledgebase_name }}</el-link
        >
        <template v-if="curDetail && curDetail.category_name">
          &nbsp; / &nbsp;</template
        >
        <el-link
          style="font-size: 16px;color: #909BA5;"
          @click="
            $router.push(
              '/dataset/detail?id=' +
                curDetail.knowledgebase_id +
                '&knowledgebase_id=' +
                curDetail.knowledgebase_id +
                '&category_id=' +
                curDetail.category_id
            )
          "
          v-if="curDetail && curDetail.category_name"
          >{{ curDetail.category_name }}</el-link
        >
      </div>

      <div class="breadcrumbbox c-detail-breadcrumbbox" v-else-if="curDetail">
        <el-link style="font-size: 16px;color: #909BA5;" @click="goback(null,$router,route.query.fpath || '/excel/detail?id='+route.query.rid)">{{curDetail.file_name}}</el-link>
        &nbsp; / &nbsp;
        <span>{{curDetail.title}}</span>
      </div>
  <div class="pageContain c-bodybox">
    <el-scrollbar>
      

      <div v-if="!isShop" class="mdbox">
        <v-md-preview :text="mkData"></v-md-preview>
      </div>

      <div v-else-if="shopDetail" class="shopCotaion">
        <div class="title">是否商品：{{ shopDetail.is_sku ? "是" : "否" }}</div>
        <div class="title">
          是否停用：{{ shopDetail.is_disabled ? "是" : "否" }}
        </div>
        <div class="title">
          是否停产：{{ shopDetail.is_stop_production ? "是" : "否" }}
        </div>
        <div class="shopbox">
          <div class="item">
            <div class="label">名称：</div>
            <div class="val">{{ shopDetail.name }}</div>
          </div>
          <div v-if="shopDetail.barcode" class="item">
            <div class="label">69码：</div>
            <div class="val">{{ shopDetail.barcode }}</div>
          </div>
          <div v-if="shopDetail.nccode" class="item">
            <div class="label">NC编码：</div>
            <div class="val">{{ shopDetail.nccode }}</div>
          </div>
          <div class="item">
            <div class="label">介绍：</div>
            <div class="val">{{ shopDetail.note }}</div>
          </div>
          <div v-for="item in shopDetail.attrs" :key="item.id" class="item">
            <div class="label">{{ item.attr_key }}：</div>
            <div class="val">{{ item.attr_value.join(",") }}</div>
          </div>
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>
<style scoped>
.shopCotaion .title {
  text-align: left;
  font-size: 20px;
  padding: 10px 20px;
}
.mdbox {
  text-align: left;
}
.backbox {
  font-size: 16px;
}
.icon-fanhui {
  font-size: 26px;
  margin-right: 5px;
}

.titlebox {
  text-align: left;
  font-size: 22px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 10px 30px;
  font-weight: bold;
}
.icon-zhishi {
  font-size: 36px;
  font-weight: bold;
  color: #1948e7;
}
.shopbox {
  text-align: left;
  font-size: 16px;
  padding: 20px;
  max-width: 1200px;
}
.shopbox .item {
  display: flex;
  align-items: inherit;
  justify-content: flex-start;
  border: 1px solid var(--el-border-color);
  border-bottom: none;
}
.shopbox .item:nth-last-child(1) {
  border-bottom: 1px solid var(--el-border-color);
}
.shopbox .item .label {
  width: 200px;
  text-align: right;
  padding: 10px 20px;
  background: rgba(75, 196, 186, 0.067);
}
.shopbox .item .val {
  word-break: break-all;
  text-align: left;
  width: calc(100% - 220px);
  padding: 10px 20px;
}
.pageContain {
  display: block;
  position: relative;
  width: 100%;
  height: calc(100% - 45px);
}
.breadcrumbbox {
  text-align: left;
  font-size: 16px;
  padding: 0 0 20px 0;
}
</style>
