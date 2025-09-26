/*eslint-disable*/
function add0(m){return m<10?'0'+m:m }
export function getWeekByDate(timeStamp){
    // 根据时间戳获取当前周几
    let date = new Date();
    if(timeStamp){
      date = new Date(timeStamp);
    }
    let weekMap={
      0:'周日',
      1:'周一',
      2:'周二',
      3:'周三',
      4:'周四',
      5:'周五',
      6:'周六',
    }
    return weekMap[date.getDay()];
  }
  
  
  export function formatDate(timeStamp, type) {
    if (/^[\d\-]+T[\d\:]+(\.\d{1,3})?\+0000$/.test(timeStamp)) {
      timeStamp = timeStamp.replace('+0000', 'Z'); // +0000和Z都代表0时区，+0000在IE不识别，替换为Z
    }
    timeStamp = new Date(timeStamp).getTime();
    timeStamp = parseInt(timeStamp) === NaN ? 0 : parseInt(timeStamp)
    let time = new Date(timeStamp);
    let y = time.getFullYear();
    let m = time.getMonth() + 1;
    let d = time.getDate();
    let h = time.getHours();
    let mm = time.getMinutes();
    let s = time.getSeconds();
  
    if (type && type.split(' ').length === 1) {
      //只有一个字符串  
      if (type.indexOf('yy') != -1) {
        // 返回年月日  否则返回时分秒
        return y +
          type.match(/yy(\S*)mm/)[1] +
          add0(m) +
          type.match(/mm(\S*)dd/)[1] +
          add0(d) +
          type.match(/dd(\S*)/)[1];
      } else if (type.indexOf('mm') != -1) {
        // 返回年月日  否则返回时分秒
        return add0(m) +
          type.match(/mm(\S*)dd/)[1] +
          add0(d) +
          type.match(/dd(\S*)/)[1];
      } else if (type.indexOf('dd') != -1) {
        // 返回年月日  否则返回时分秒
        return add0(d) +
          type.match(/dd(\S*)/)[1];
      } else {
        return add0(h) +
          type.match(/hh(\S*)mm/)[1] +
          add0(mm) +
          type.match(/mm(\S*)ss/)[1] +
          add0(s) +
          type.match(/ss(\S*)/)[1]
      }
    } else if (type && type.split(' ').length > 1) {
      // 返回年月日时分秒
      return y +
        type.match(/yy(\S*)mm/)[1] +
        add0(m) +
        type.match(/mm(\S*)dd/)[1] +
        add0(d) +
        type.match(/dd(\S*)/)[1] +
        ' ' +
        add0(h) +
        type.match(/hh(\S*)mm/)[1] +
        add0(mm) +
        type.match(/mm(\S*)ss/)[1] +
        add0(s) +
        type.match(/ss(\S*)/)[1]
    } else {
      return y + '-' + add0(m) + '-' + add0(d) + ' ' + add0(h) + ':' + add0(mm) + ':' + add0(s);
    }
  }

export function timeStampToHour(timeStamp,type){
    // 时间戳转换 时分秒
    timeStamp = isNaN(timeStamp) ? 0 : parseInt(timeStamp);
    if(timeStamp<=0){
        return '';
    }
    var hour = add0(parseInt(timeStamp/(1000*60*60),10));
    var minute = add0(parseInt((timeStamp%(1000*60*60))/(1000*60),10));
    var sec = add0(parseInt((timeStamp%(1000*60*60)%(1000*60))/(1000),10));

    return hour+'小时'+minute+'分';
}

/**
* 日期范围工具类
*/
export function getTimeRange() {
    /***
    * 获得当前时间
    */
    let dateRangeUtil = {};
    dateRangeUtil.getCurrentDate = function () {
        return new Date();
    };
  
    /***
    * 获得本周起止时间
    */
    dateRangeUtil.getCurrentWeek = function () {
        //起止日期数组
        let startStop = new Array();
        //获取当前时间
        let currentDate = dateRangeUtil.getCurrentDate();
        //返回date是一周中的某一天
        let week = currentDate.getDay();
        //返回date是一个月中的某一天
        let month = currentDate.getDate();
  
        //一天的毫秒数
        let millisecond = 1000 * 60 * 60 * 24;
        //减去的天数
        let minusDay = week != 0 ? week - 1 : 6;
        //alert(minusDay);
        //本周 周一
        let monday = new Date(currentDate.getTime() - (minusDay * millisecond));
        //本周 周日
        let sunday = new Date(monday.getTime() + (6 * millisecond));
        //添加本周时间
        startStop.push(formatDate(monday)); //本周起始时间
        //添加本周最后一天时间
        startStop.push(formatDate(sunday)); //本周终止时间
        //返回
        return startStop;
    };
  
    /***
    * 获得本月的起止时间
    */
    dateRangeUtil.getCurrentMonth = function () {
        //起止日期数组
        let startStop = new Array();
        //获取当前时间
        let currentDate = dateRangeUtil.getCurrentDate();
        //获得当前月份0-11
        let currentMonth = currentDate.getMonth();
        //获得当前年份4位年
        let currentYear = currentDate.getFullYear();
        //求出本月第一天
        let firstDay = new Date(currentYear, currentMonth, 1);
  
  
        //当为12月的时候年份需要加1
        //月份需要更新为0 也就是下一年的第一个月
        if (currentMonth == 11) {
            currentYear++;
            currentMonth = 0; //就为
        } else {
            //否则只是月份增加,以便求的下一月的第一天
            currentMonth++;
        }
  
  
        //一天的毫秒数
        let millisecond = 1000 * 60 * 60 * 24;
        //下月的第一天
        let nextMonthDayOne = new Date(currentYear, currentMonth, 1);
        //求出上月的最后一天
        let lastDay = new Date(nextMonthDayOne.getTime() - millisecond);
  
        //添加至数组中返回
        startStop.push(formatDate(firstDay));
        startStop.push(formatDate(lastDay));
        //返回
        return startStop;
    };
  
    /**
    * 得到本季度开始的月份
    * @param month 需要计算的月份
    ***/
    dateRangeUtil.getQuarterSeasonStartMonth = function (month) {
        let quarterMonthStart = 0;
        let spring = 0; //春
        let summer = 3; //夏
        let fall = 6;   //秋
        let winter = 9; //冬
        //月份从0-11
        if (month < 3) {
            return spring;
        }
  
        if (month < 6) {
            return summer;
        }
  
        if (month < 9) {
            return fall;
        }
  
        return winter;
    };
  
    /**
    * 获得该月的天数
    * @param year年份
    * @param month月份
    * */
    dateRangeUtil.getMonthDays = function (year, month) {
        //本月第一天 1-31
        let relativeDate = new Date(year, month, 1);
        //获得当前月份0-11
        let relativeMonth = relativeDate.getMonth();
        //获得当前年份4位年
        let relativeYear = relativeDate.getFullYear();
  
        //当为12月的时候年份需要加1
        //月份需要更新为0 也就是下一年的第一个月
        if (relativeMonth == 11) {
            relativeYear++;
            relativeMonth = 0;
        } else {
            //否则只是月份增加,以便求的下一月的第一天
            relativeMonth++;
        }
        //一天的毫秒数
        let millisecond = 1000 * 60 * 60 * 24;
        //下月的第一天
        let nextMonthDayOne = new Date(relativeYear, relativeMonth, 1);
        //返回得到上月的最后一天,也就是本月总天数
        return new Date(nextMonthDayOne.getTime() - millisecond).getDate();
    };
  
    /**
    * 获得本季度的起止日期
    */
    dateRangeUtil.getCurrentSeason = function () {
        //起止日期数组
        let startStop = new Array();
        //获取当前时间
        let currentDate = dateRangeUtil.getCurrentDate();
        //获得当前月份0-11
        let currentMonth = currentDate.getMonth();
        //获得当前年份4位年
        let currentYear = currentDate.getFullYear();
        //获得本季度开始月份
        let quarterSeasonStartMonth = dateRangeUtil.getQuarterSeasonStartMonth(currentMonth);
        //获得本季度结束月份
        let quarterSeasonEndMonth = quarterSeasonStartMonth + 2;
  
        //获得本季度开始的日期
        let quarterSeasonStartDate = new Date(currentYear, quarterSeasonStartMonth, 1);
        //获得本季度结束的日期
        let quarterSeasonEndDate = new Date(currentYear, quarterSeasonEndMonth, dateRangeUtil.getMonthDays(currentYear, quarterSeasonEndMonth));
        //加入数组返回
        startStop.push(quarterSeasonStartDate);
        startStop.push(quarterSeasonEndDate);
        //返回
        return startStop;
    };
  
    /***
    * 得到本年的起止日期
    *
    */
    dateRangeUtil.getCurrentYear = function (year) {
        //起止日期数组
        let startStop = new Array();
        //获取当前时间
        let currentDate = dateRangeUtil.getCurrentDate();
        
        //获得当前年份4位年
        let currentYear = currentDate.getFullYear();
        if(year){
            currentYear = year;
        }
        //本年第一天
        let currentYearFirstDate = new Date(currentYear, 0, 1);
        //本年最后一天
        let currentYearLastDate = new Date(currentYear, 11, 31);
        //添加至数组
        startStop.push(formatDate(currentYearFirstDate));
        startStop.push(formatDate(currentYearLastDate));
        //返回
        return startStop;
    };
  
    /**
    * 返回上一个月的第一天Date类型
    * @param year 年
    * @param month 月
    **/
    dateRangeUtil.getPriorMonthFirstDay = function (year, month) {
        //年份为0代表,是本年的第一月,所以不能减
        if (month == 0) {
            month = 11; //月份为上年的最后月份
            year--; //年份减1
            return new Date(year, month, 1);
        }
        //否则,只减去月份
        month--;
        return new Date(year, month, 1); ;
    };
  
    /**
    * 获得上一月的起止日期
    * ***/
    dateRangeUtil.getPreviousMonth = function () {
        //起止日期数组
        let startStop = new Array();
        //获取当前时间
        let currentDate = dateRangeUtil.getCurrentDate();
        //获得当前月份0-11
        let currentMonth = currentDate.getMonth();
        //获得当前年份4位年
        let currentYear = currentDate.getFullYear();
        //获得上一个月的第一天
        let priorMonthFirstDay = dateRangeUtil.getPriorMonthFirstDay(currentYear, currentMonth);
        //获得上一月的最后一天
        let priorMonthLastDay = new Date(priorMonthFirstDay.getFullYear(), priorMonthFirstDay.getMonth(), dateRangeUtil.getMonthDays(priorMonthFirstDay.getFullYear(), priorMonthFirstDay.getMonth()));
        //添加至数组
        startStop.push(formatDate(priorMonthFirstDay));
        startStop.push(formatDate(priorMonthLastDay));
        //返回
        return startStop;
    };
  
  
    /**
    * 获得上一周的起止日期
    * **/
    dateRangeUtil.getPreviousWeek = function () {
        //起止日期数组
        let startStop = new Array();
        //获取当前时间
        let currentDate = dateRangeUtil.getCurrentDate();
        //返回date是一周中的某一天
        let week = currentDate.getDay();
        //返回date是一个月中的某一天
        let month = currentDate.getDate();
        //一天的毫秒数
        let millisecond = 1000 * 60 * 60 * 24;
        //减去的天数
        let minusDay = week != 0 ? week - 1 : 6;
        //获得当前周的第一天
        let currentWeekDayOne = new Date(currentDate.getTime() - (millisecond * minusDay));
        //上周最后一天即本周开始的前一天
        let priorWeekLastDay = new Date(currentWeekDayOne.getTime() - millisecond);
        //上周的第一天
        let priorWeekFirstDay = new Date(priorWeekLastDay.getTime() - (millisecond * 6));
  
        //添加至数组
        startStop.push(formatDate(priorWeekFirstDay));
        startStop.push(formatDate(priorWeekLastDay));
  
        return startStop;
    };
  
    /**
    * 得到上季度的起始日期
    * year 这个年应该是运算后得到的当前本季度的年份
    * month 这个应该是运算后得到的当前季度的开始月份
    * */
    dateRangeUtil.getPriorSeasonFirstDay = function (year, month) {
        let quarterMonthStart = 0;
        let spring = 0; //春
        let summer = 3; //夏
        let fall = 6;   //秋
        let winter = 9; //冬
        //月份从0-11
        switch (month) {//季度的其实月份
            case spring:
                //如果是第一季度则应该到去年的冬季
                year--;
                month = winter;
                break;
            case summer:
                month = spring;
                break;
            case fall:
                month = summer;
                break;
            case winter:
                month = fall;
                break;
  
        };
  
        return new Date(year, month, 1);
    };
  
    /**
    * 得到上季度的起止日期
    * **/
    dateRangeUtil.getPreviousSeason = function () {
        //起止日期数组
        let startStop = new Array();
        //获取当前时间
        let currentDate = dateRangeUtil.getCurrentDate();
        //获得当前月份0-11
        let currentMonth = currentDate.getMonth();
        //获得当前年份4位年
        let currentYear = currentDate.getFullYear();
        //上季度的第一天
        let priorSeasonFirstDay = dateRangeUtil.getPriorSeasonFirstDay(currentYear, currentMonth);
        //上季度的最后一天
        let priorSeasonLastDay = new Date(priorSeasonFirstDay.getFullYear(), priorSeasonFirstDay.getMonth() + 2, dateRangeUtil.getMonthDays(priorSeasonFirstDay.getFullYear(), priorSeasonFirstDay.getMonth() + 2));
        //添加至数组
        startStop.push(priorSeasonFirstDay);
        startStop.push(priorSeasonLastDay);
        return startStop;
    };
  
    /**
    * 得到去年的起止日期
    * **/
    dateRangeUtil.getPreviousYear = function () {
        //起止日期数组
        let startStop = new Array();
        //获取当前时间
        let currentDate = dateRangeUtil.getCurrentDate();
        //获得当前年份4位年
        let currentYear = currentDate.getFullYear();
        currentYear--;
        let priorYearFirstDay = new Date(currentYear, 0, 1);
        let priorYearLastDay = new Date(currentYear, 11, 1);
        //添加至数组
        startStop.push(formatDate(priorYearFirstDay));
        startStop.push(formatDate(priorYearLastDay));
        return startStop;
    };
  
    return dateRangeUtil;
};



