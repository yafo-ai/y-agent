<script setup>
import { goback } from "@/components/comp.js";
</script>

<template>
  <div class="page404">
        <h3>抱歉，您访问的页面出错了~</h3>
        <div class="ulbox">
        <ul>
          <li>权限错误</li>
          <li>页面已经下线</li>
          <li>其他未知错误</li>
        </ul>

        <br>
        <br>

        <el-button block @click="goback('/dataset/list',$router)" type="primary">返回</el-button>
        </div>
        
    </div>
</template>

<style scoped>
.page404{
  width: 600px;
  margin: 100px auto;
}
 h3{
    text-align: center;
    font-size: 20px;
    padding: 20px;
  }
  .page404 img{
    width: 100%;
  }
  h3{
    font-size: 22px;
    font-weight: bold;
  }
  .ulbox{
    padding: 10px 50px 10px 156px;
    text-align: left;
  }
  li{
    font-size: 12px;
    color: #999;
    position: relative;
    padding: 5px 0;
    padding-left: 20px;
  }
  li:before{
    content: "";
    position: absolute;
    width: 10px;
    height: 10px;
    background: #ccc;
    left: 0;
    border-radius: 100%;
    top: 8px;
  }
  .btn-primary{
    width: 200px;
    margin: 40px auto;
  }
</style>
