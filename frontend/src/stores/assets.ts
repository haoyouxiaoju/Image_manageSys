import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Asset, AssetVersion, Collection, SearchResult } from '@/types'

// ===== 确定性哈希（替代 Math.random） =====
function hashStr(s: string): number {
  let h = 5381
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h) + s.charCodeAt(i)
  return Math.abs(h)
}

// ===== 全量模拟素材（应用唯一数据源） =====
function buildMockAssets(): Asset[] {
  return [
    { id:1,  name:'科技感蓝色背景图',    desc:'深蓝色渐变科技感背景，粒子光效',     thumb:'https://picsum.photos/seed/tech1/400/300',  author:'小明', date:'2026-05-03', tags:['科技感'],         source:'设计部',   size:'2.4 MB', format:'PNG',
      clipDesc:'深蓝色渐变背景，带有发光粒子效果，呈现科技感和未来感', clipStyle:'数字合成图', clipColor:'深蓝/青色为主色调', clipTags:['科技感','背景','粒子','深蓝'],
      versions:[{version:'v1.2',note:'优化粒子密度，调整色调',date:'2026-05-03'},{version:'v1.1',note:'增加粒子光效层',date:'2026-04-28'},{version:'v1.0',note:'初版',date:'2026-04-20'}] },
    { id:2,  name:'2026年会大合影',       desc:'公司2026年度年会全员合影',           thumb:'https://picsum.photos/seed/party2/400/300',  author:'小红', date:'2026-04-28', tags:['年会活动','人物'], source:'行政部',   size:'5.1 MB', format:'JPG',
      clipDesc:'室内大合照，人群穿着正式服装，舞台灯光，横幅可见', clipStyle:'室内摄影', clipColor:'暖色调/黄色灯光', clipTags:['人群','室内','年会','合影','正式'],
      versions:[{version:'v1.0',note:'原始照片',date:'2026-04-28'}] },
    { id:3,  name:'产品白底图系列-A款',   desc:'A款产品白底棚拍图，适合电商使用',     thumb:'https://picsum.photos/seed/prod3/400/300',  author:'小明', date:'2026-04-25', tags:['产品图'],         source:'电商部',   size:'1.8 MB', format:'JPG',
      clipDesc:'白色背景上的产品展示照片，光线均匀，专业商业摄影风格', clipStyle:'商业摄影棚拍', clipColor:'白色/中性光', clipTags:['产品','白底','商业摄影','电商'],
      versions:[{version:'v2.0',note:'重新布光拍摄',date:'2026-04-25'},{version:'v1.0',note:'首版棚拍',date:'2026-04-10'}] },
    { id:4,  name:'双十一促销海报',        desc:'2025双十一大促主视觉海报',           thumb:'https://picsum.photos/seed/poster4/400/300', author:'运营部', date:'2026-03-18', tags:['海报'],          source:'运营部',   size:'3.2 MB', format:'PSD',
      clipDesc:'促销海报设计，醒目的大字体价格和折扣信息，红金配色', clipStyle:'平面设计/海报', clipColor:'红色/金色', clipTags:['促销','海报','电商','大促','红色'],
      versions:[{version:'v3.0',note:'最终定稿',date:'2026-03-18'},{version:'v2.0',note:'调整价格区域',date:'2026-03-10'},{version:'v1.0',note:'初稿',date:'2026-03-01'}] },
    { id:5,  name:'App登录页设计稿',       desc:'移动端App登录注册页面UI设计',        thumb:'https://picsum.photos/seed/ui5/400/300',     author:'设计部', date:'2026-04-12', tags:['UI设计'],        source:'设计部',   size:'0.9 MB', format:'Figma',
      clipDesc:'移动应用界面截图，包含登录表单、按钮和品牌Logo', clipStyle:'UI设计稿/截图', clipColor:'白色/品牌色', clipTags:['UI','移动端','登录','表单','App'],
      versions:[{version:'v1.1',note:'调整按钮圆角',date:'2026-04-12'},{version:'v1.0',note:'初版',date:'2026-04-08'}] },
    { id:6,  name:'深圳办公室环境照',      desc:'深圳南山办公室全貌及功能区展示',     thumb:'https://picsum.photos/seed/office6/400/300', author:'行政部', date:'2026-04-05', tags:['城市建筑'],      source:'行政部',   size:'3.8 MB', format:'JPG',
      clipDesc:'现代办公空间，开放式工位和会议室，大窗户自然采光', clipStyle:'室内建筑摄影', clipColor:'白色/木色/自然光', clipTags:['办公室','室内','现代','自然光'],
      versions:[{version:'v1.0',note:'办公室实拍',date:'2026-04-05'}] },
    { id:7,  name:'春季新品发布海报',      desc:'2026春季新品系列主视觉海报',         thumb:'https://picsum.photos/seed/poster7/400/300', author:'设计部', date:'2026-03-28', tags:['海报','产品图'],  source:'设计部',   size:'4.1 MB', format:'PSD',
      clipDesc:'春日主题海报，花卉元素和粉嫩色调，展示春季新品', clipStyle:'平面设计/海报', clipColor:'粉色/绿色/柔光', clipTags:['春季','海报','新品','花卉','粉色'],
      versions:[{version:'v2.0',note:'终稿',date:'2026-03-28'},{version:'v1.0',note:'初稿',date:'2026-03-20'}] },
    { id:8,  name:'云南团建风景照',        desc:'公司团建云南大理风光摄影',           thumb:'https://picsum.photos/seed/nature8/400/300', author:'小红', date:'2026-03-15', tags:['自然风景','人物'], source:'行政部',   size:'6.2 MB', format:'JPG',
      clipDesc:'自然风光照片，蓝天白云下的湖泊和山脉，有游客', clipStyle:'风光摄影', clipColor:'蓝色/绿色/自然光', clipTags:['风景','湖泊','山脉','户外','蓝天'],
      versions:[{version:'v1.0',note:'团建随拍',date:'2026-03-15'}] },
    { id:9,  name:'后台管理Dashboard设计', desc:'企业内部管理系统仪表盘页面设计',      thumb:'https://picsum.photos/seed/ui9/400/300',     author:'设计部', date:'2026-03-08', tags:['UI设计','科技感'], source:'设计部',   size:'1.5 MB', format:'PNG',
      clipDesc:'数据仪表盘界面设计，图表卡片布局，深色主题', clipStyle:'UI设计稿', clipColor:'深色/蓝色图表', clipTags:['仪表盘','后台','数据','深色主题','图表'],
      versions:[{version:'v1.0',note:'初版',date:'2026-03-08'}] },
    { id:10, name:'年度报告封面设计',      desc:'2025年度企业报告封面与内页模板',     thumb:'https://picsum.photos/seed/report10/400/300', author:'小明', date:'2026-02-22', tags:['海报','科技感'],   source:'品牌部',   size:'2.0 MB', format:'PDF',
      clipDesc:'商务报告封面设计，简洁排版，数据可视化元素', clipStyle:'平面设计', clipColor:'深蓝/白色/金色点缀', clipTags:['报告','封面','商务','简洁','品牌'],
      versions:[{version:'v1.0',note:'定稿',date:'2026-02-22'}] },
    { id:11, name:'上海外滩建筑摄影',      desc:'上海外滩历史建筑群高清摄影',         thumb:'https://picsum.photos/seed/bund11/400/300', author:'小明', date:'2026-02-10', tags:['城市建筑'],      source:'外部团队', size:'7.5 MB', format:'JPG',
      clipDesc:'城市建筑群外观，古典欧式建筑，黄浦江畔，黄昏时分', clipStyle:'建筑摄影', clipColor:'暖黄/灰色石墙', clipTags:['建筑','外滩','城市','黄昏','古典'],
      versions:[{version:'v1.0',note:'外拍素材',date:'2026-02-10'}] },
    { id:12, name:'员工团队展示页设计',    desc:'企业官网团队介绍页面设计稿',         thumb:'https://picsum.photos/seed/team12/400/300', author:'设计部', date:'2026-01-18', tags:['UI设计','人物'],   source:'设计部',   size:'1.1 MB', format:'PNG',
      clipDesc:'网页设计稿，人员头像网格布局，简洁专业风格', clipStyle:'UI设计稿', clipColor:'白色/品牌色', clipTags:['网页','团队','头像','简约','企业'],
      versions:[{version:'v2.0',note:'新增成员照片位',date:'2026-01-25'},{version:'v1.0',note:'初稿',date:'2026-01-18'}] },
    { id:13, name:'年终庆典主KV设计',      desc:'2025年终庆典活动主视觉及物料',       thumb:'https://picsum.photos/seed/event13/400/300', author:'运营部', date:'2026-01-05', tags:['年会活动','海报'], source:'运营部',   size:'3.6 MB', format:'PSD',
      clipDesc:'庆典活动主题海报，金色装饰元素和节日氛围', clipStyle:'平面设计/海报', clipColor:'金色/红色/深蓝', clipTags:['年终','庆典','海报','金色','节日'],
      versions:[{version:'v1.0',note:'最终稿',date:'2026-01-05'}] },
    { id:14, name:'杭州西湖晨曦风光',      desc:'西湖清晨雾中景色航拍素材',           thumb:'https://picsum.photos/seed/lake14/400/300', author:'小明', date:'2025-12-20', tags:['自然风景'],      source:'外部团队', size:'8.0 MB', format:'JPG',
      clipDesc:'航拍视角的湖泊景观，清晨薄雾笼罩水面，远山朦胧', clipStyle:'航拍摄影', clipColor:'蓝灰/白雾/晨光', clipTags:['航拍','湖泊','晨雾','自然','远景'],
      versions:[{version:'v1.0',note:'航拍原始素材',date:'2025-12-20'}] },
    { id:15, name:'智能家居控制界面',      desc:'智能家居App控制面板UI设计稿',       thumb:'https://picsum.photos/seed/smart15/400/300', author:'设计部', date:'2025-12-08', tags:['UI设计','科技感'], source:'设计部',   size:'1.3 MB', format:'PNG',
      clipDesc:'移动应用界面，家居设备控制面板，深色主题搭配发光图标', clipStyle:'UI设计稿', clipColor:'深色/霓虹色图标', clipTags:['智能家居','UI','控制面板','深色','App'],
      versions:[{version:'v1.0',note:'初版',date:'2025-12-08'}] },
    { id:16, name:'热拿铁咖啡特写',        desc:'一杯热气腾腾的拿铁咖啡，表面有精致拉花', thumb:'https://picsum.photos/seed/coffee16/400/300', author:'小红', date:'2026-05-04', tags:['食物饮品'],  source:'外包团队', size:'3.1 MB', format:'JPG',
      clipDesc:'一杯热咖啡的特写照片，表面有拉花图案，杯中冒着热气，木质桌面背景', clipStyle:'美食摄影', clipColor:'棕色/奶白色/暖色调', clipTags:['咖啡','拿铁','拉花','热饮','特写','木质桌面'],
      versions:[{version:'v1.0',note:'商业拍摄',date:'2026-05-04'}] },
    { id:17, name:'橘猫趴在窗台上',        desc:'一只橘色虎斑猫慵懒地趴在阳光下的窗台上', thumb:'https://picsum.photos/seed/cat17/400/300', author:'小明', date:'2026-05-02', tags:['动物'],      source:'个人拍摄', size:'2.8 MB', format:'JPG',
      clipDesc:'一只橘色虎斑猫趴在室内窗台上，阳光从窗户照进来，猫咪眯着眼睛', clipStyle:'宠物摄影', clipColor:'橘色/自然光/暖色调', clipTags:['猫','橘猫','宠物','窗台','阳光','慵懒'],
      versions:[{version:'v1.0',note:'日常拍摄',date:'2026-05-02'}] },
    { id:18, name:'金毛犬草地奔跑',        desc:'一只金毛寻回犬在绿色草地上欢快地奔跑', thumb:'https://picsum.photos/seed/dog18/400/300', author:'小红', date:'2026-04-30', tags:['动物'],      source:'外部团队', size:'4.5 MB', format:'JPG',
      clipDesc:'金毛犬在户外草地上奔跑，阳光明媚，狗毛在光线下闪闪发光', clipStyle:'宠物摄影/户外', clipColor:'金色/绿色/蓝天', clipTags:['狗','金毛','草地','户外','奔跑','阳光'],
      versions:[{version:'v1.0',note:'户外拍摄',date:'2026-04-30'}] },
    { id:19, name:'手工牛肉汉堡套餐',      desc:'餐厅拍摄的招牌牛肉汉堡配薯条和可乐',   thumb:'https://picsum.photos/seed/burger19/400/300', author:'运营部', date:'2026-04-22', tags:['食物饮品'],  source:'餐饮合作方',size:'3.3 MB', format:'JPG',
      clipDesc:'汉堡特写照片，芝麻面包夹着牛肉饼、生菜和芝士，旁边有薯条和饮料', clipStyle:'美食摄影', clipColor:'金黄色/绿色/暖色调', clipTags:['汉堡','牛肉','薯条','快餐','美食摄影','套餐'],
      versions:[{version:'v1.0',note:'商业菜品拍摄',date:'2026-04-22'}] },
    { id:20, name:'红色跑车展厅展示',      desc:'一辆红色运动跑车在展厅灯光下的多角度展示', thumb:'https://picsum.photos/seed/car20/400/300', author:'设计部', date:'2026-04-18', tags:['交通工具'],  source:'品牌合作方',size:'5.0 MB', format:'JPG',
      clipDesc:'红色跑车在室内展厅展示，灯光打亮车身曲线，展示运动感线条', clipStyle:'汽车摄影', clipColor:'红色/黑色/展厅灯光', clipTags:['跑车','红色','展厅','轿车','运动','曲线'],
      versions:[{version:'v1.0',note:'品牌素材授权',date:'2026-04-18'}] },
    { id:21, name:'北欧风客厅布置',        desc:'简约北欧风格客厅全貌，白色和木色为主',  thumb:'https://picsum.photos/seed/living21/400/300', author:'小明', date:'2026-04-15', tags:['家居生活'],  source:'设计部',   size:'3.6 MB', format:'JPG',
      clipDesc:'明亮客厅室内设计，白色沙发、木地板、绿植点缀，简约现代风格', clipStyle:'室内设计摄影', clipColor:'白色/木色/绿色点缀', clipTags:['客厅','北欧','简约','室内设计','白色','木地板'],
      versions:[{version:'v1.0',note:'设计案例采集',date:'2026-04-15'}] },
  ]
}

// ===== 语义搜索关键词扩展表 =====
const semanticKeywords: Record<string, string[]> = {
  '蓝色':['科技','背景','深蓝','冷色调','渐变'], '科技':['蓝色','背景','粒子','仪表','数据','深色','未来'],
  '年会':['合影','人群','活动','庆典','聚会','舞台'], '合影':['人群','照片','团队','聚会','年会'],
  '产品':['白色','展示','商业','电商','棚拍'], '白色':['产品','展示','棚拍','背景','简约'],
  '海报':['促销','设计','广告','视觉','平面','营销'], '登录':['UI','App','移动','表单','界面'],
  '设计':['UI','界面','平面','排版','网页','创意'], '风景':['自然','户外','山水','摄影','蓝天','湖泊'],
  '建筑':['城市','大楼','古典','外景','欧式'], '促销':['海报','电商','广告','营销','大促'],
  '春季':['花卉','粉色','新品','温暖'], '智能':['科技','家居','App','控制','设备'],
  '界面':['UI','设计','面板','App','控制'], '航拍':['风景','高空','俯瞰','自然','雾','湖泊'],
  '咖啡':['拿铁','热饮','拉花','杯子','饮品','棕色','饮料'], '拿铁':['咖啡','拉花','热饮','奶泡','杯子'],
  '猫':['猫咪','橘猫','宠物','窗台','虎斑','动物','猫科'], '猫咪':['猫','橘猫','宠物','动物','慵懒'],
  '狗':['犬','金毛','宠物','奔跑','草地','户外','动物','犬科'], '金毛':['狗','犬','宠物','奔跑','草地','金色','阳光'],
  '汉堡':['薯条','快餐','食物','套餐','餐饮','牛肉','可乐'], '跑车':['红色','展厅','轿车','运动','汽车','展示','曲线'],
  '客厅':['北欧','简约','室内','家居','白色','设计','木质'], '宠物':['猫','狗','动物','猫科','犬科'],
  '食物':['汉堡','咖啡','薯条','快餐','饮品','餐饮','套餐'], '汽车':['跑车','轿车','红色','展厅','运动'],
  '家居':['客厅','北欧','室内','简约','白色','木色','装修'],
}

const reasonMap: Record<string, string> = {
  '蓝色':'色调匹配','科技':'风格匹配','背景':'场景匹配','年会':'场景匹配','合影':'内容匹配',
  '产品':'内容匹配','白色':'色调匹配','海报':'类型匹配','登录':'功能匹配','UI':'类型匹配',
  '风景':'场景匹配','建筑':'场景匹配','设计':'类型匹配','促销':'场景匹配','春季':'季节匹配',
  '智能':'主题匹配','航拍':'视角匹配','App':'类型匹配','咖啡':'物体识别：咖啡','拿铁':'物体识别：拿铁',
  '猫':'物体识别：猫','猫咪':'物体识别：猫','橘猫':'物体识别：橘猫','狗':'物体识别：狗','金毛':'物体识别：金毛犬',
  '汉堡':'物体识别：汉堡','薯条':'物体识别：薯条','跑车':'物体识别：跑车','汽车':'物体识别：汽车',
  '客厅':'场景匹配','家居':'场景匹配','宠物':'物体识别','动物':'物体识别',
  '户外':'场景匹配','室内':'场景匹配','草地':'场景匹配',
}

// ===== Pinia Store =====
export const useAssetStore = defineStore('assets', () => {
  // ---- 数据 ----
  const allAssets = ref<Asset[]>(buildMockAssets())
  const allTags = ref<string[]>([
    '科技感','产品图','海报','UI设计','年会活动','人物','自然风景','城市建筑','动物','食物饮品','交通工具','家居生活'
  ])

  const mockCollections = ref<Collection[]>([
    { id:1, name:'2026春季新品素材',   desc:'春季新品发布的全部视觉物料',                 assetIds:[7,3],                      created:'2026-03-20', creator:'小明' },
    { id:2, name:'年会活动合集',       desc:'年会合影、庆典物料统一管理',                 assetIds:[2,13],                     created:'2026-01-10', creator:'小红' },
    { id:3, name:'UI设计稿归档',       desc:'App和后台管理系统的设计稿',                   assetIds:[5,9,12,15],                created:'2026-02-05', creator:'设计部' },
    { id:4, name:'电商营销海报',       desc:'促销和营销相关海报素材',                      assetIds:[4,7,10],                   created:'2026-03-01', creator:'运营部' },
    { id:5, name:'宠物摄影',            desc:'猫狗宠物相关摄影素材',                        assetIds:[17,18],                    created:'2026-05-01', creator:'小明' },
    { id:6, name:'风光与建筑摄影',     desc:'自然风光和城市建筑摄影合集',                  assetIds:[8,11,14],                  created:'2026-02-15', creator:'小明' },
  ])

  // ---- 筛选 & 分页 ----
  const selectedTags = ref<string[]>([])
  const globalSearch = ref('')
  const pageSize = 10
  const currentPage = ref(1)

  // ---- 搜索 ----
  const searchQuery = ref('')
  const searchResults = ref<SearchResult[]>([])
  const searching = ref(false)

  // ---- 计算 ----
  const filteredAssets = computed(() => {
    let arr = allAssets.value
    if (selectedTags.value.length > 0) {
      arr = arr.filter(a => selectedTags.value.some(t => a.tags.includes(t)))
    }
    if (globalSearch.value) {
      const q = globalSearch.value.toLowerCase()
      arr = arr.filter(a =>
        a.name.toLowerCase().includes(q) ||
        a.desc.toLowerCase().includes(q) ||
        (a.clipDesc && a.clipDesc.toLowerCase().includes(q))
      )
    }
    return arr
  })

  const pagedAssets = computed(() => {
    const start = (currentPage.value - 1) * pageSize
    return filteredAssets.value.slice(start, start + pageSize)
  })

  const monthNewCount = computed(() => {
    const now = new Date()
    return allAssets.value.filter(a => {
      const d = new Date(a.date)
      return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth()
    }).length
  })

  const clipReadyCount = computed(() => allAssets.value.filter(a => a.clipDesc).length)

  // ---- 素材 CRUD ----
  function getAssetById(id: number): Asset | undefined {
    return allAssets.value.find(a => a.id === id)
  }

  function updateAsset(id: number, data: Partial<Pick<Asset, 'name' | 'desc' | 'tags' | 'source'>>) {
    const a = allAssets.value.find(x => x.id === id)
    if (!a) return
    if (data.name !== undefined) a.name = data.name
    if (data.desc !== undefined) a.desc = data.desc
    if (data.tags !== undefined) a.tags = [...data.tags]
    if (data.source !== undefined) a.source = data.source
  }

  function deleteAsset(id: number) {
    const idx = allAssets.value.findIndex(x => x.id === id)
    if (idx >= 0) {
      allAssets.value.splice(idx, 1)
      // 清理关联数据
      mockCollections.value.forEach(c => {
        c.assetIds = c.assetIds.filter(aid => aid !== id)
      })
    }
  }

  function addAsset(asset: Asset) {
    allAssets.value.unshift(asset)
    // 自动加入"未分类"标签
    if (!allTags.value.includes('未分类')) {
      // 已在 allTags 中，不操作
    }
  }

  function addAssetTag(assetId: number, tag: string) {
    const a = allAssets.value.find(x => x.id === assetId)
    if (a && !a.tags.includes(tag)) {
      a.tags = [...a.tags, tag]
      if (!allTags.value.includes(tag)) allTags.value.push(tag)
    }
  }

  function removeAssetTag(assetId: number, tag: string) {
    const a = allAssets.value.find(x => x.id === assetId)
    if (a) a.tags = a.tags.filter(t => t !== tag)
  }

  function addVersion(assetId: number, version: AssetVersion) {
    const a = allAssets.value.find(x => x.id === assetId)
    if (a) a.versions = [...a.versions, version]
  }

  // ---- 标签 ----
  function toggleTag(tag: string) {
    const i = selectedTags.value.indexOf(tag)
    i >= 0 ? selectedTags.value.splice(i, 1) : selectedTags.value.push(tag)
    currentPage.value = 1
  }

  function clearFilters() {
    selectedTags.value = []
    globalSearch.value = ''
    currentPage.value = 1
  }

  // ---- 分组 ----
  function getCollectionById(id: number): Collection | undefined {
    return mockCollections.value.find(c => c.id === id)
  }

  function getCollectionAssets(col: Collection): Asset[] {
    return col.assetIds.map(id => getAssetById(id)).filter(Boolean) as Asset[]
  }

  function createCollection(name: string, desc: string, creator: string) {
    mockCollections.value.push({
      id: Date.now(),
      name, desc,
      assetIds: [],
      created: new Date().toISOString().split('T')[0],
      creator,
    })
  }

  function addToCollection(collectionId: number, assetId: number) {
    const c = mockCollections.value.find(x => x.id === collectionId)
    if (c && !c.assetIds.includes(assetId)) {
      c.assetIds.push(assetId)
    }
  }

  function removeFromCollection(collectionId: number, assetId: number) {
    const c = mockCollections.value.find(x => x.id === collectionId)
    if (c) c.assetIds = c.assetIds.filter(id => id !== assetId)
  }

  function deleteCollection(id: number) {
    mockCollections.value = mockCollections.value.filter(c => c.id !== id)
  }

  // ---- 搜索（确定性评分） ----
  function doSearch(query: string) {
    if (!query.trim()) return
    searchQuery.value = query
    searching.value = true

    setTimeout(() => {
      const q = query
      let expandedTerms = [q]
      for (const [kw, terms] of Object.entries(semanticKeywords)) {
        if (q.includes(kw)) expandedTerms.push(...terms)
      }

      const results: SearchResult[] = allAssets.value.map(a => {
        const st = (a.name + a.desc + (a.clipDesc || '') + (a.clipTags || []).join(' ') + (a.clipStyle || '') + (a.clipColor || '')).toLowerCase()
        let matchScore = 0
        const reasons: string[] = []
        expandedTerms.forEach(t => {
          if (st.includes(t.toLowerCase())) { matchScore += 25; reasons.push(t) }
        })
        if (a.name.toLowerCase().includes(q.toLowerCase())) matchScore += 20
        if ((a.clipDesc || '').toLowerCase().includes(q.toLowerCase())) matchScore += 15
        a.tags.forEach(t => { if (expandedTerms.some(e => t.includes(e))) matchScore += 10 })

        const matchedReasons = [...new Set(reasons)].slice(0, 3).map(r => reasonMap[r] || r).filter(Boolean)
        const offset = hashStr(q + '_' + a.id) % 10
        const score = Math.min(99, Math.max(40, 50 + matchScore + offset))
        return { ...a, score, matchReasons: matchedReasons.length > 0 ? matchedReasons : ['语义关联'] }
      }).filter(r => r.score > 50).sort((a, b) => b.score - a.score)

      searchResults.value = results
      searching.value = false
    }, 400)
  }

  return {
    // 数据
    allAssets, allTags, mockCollections,
    // 筛选
    selectedTags, globalSearch, pageSize, currentPage,
    // 计算
    filteredAssets, pagedAssets, monthNewCount, clipReadyCount,
    // 搜索
    searchQuery, searchResults, searching,
    // 素材 CRUD
    getAssetById, updateAsset, deleteAsset, addAsset, addAssetTag, removeAssetTag, addVersion,
    // 标签
    toggleTag, clearFilters,
    // 分组
    getCollectionById, getCollectionAssets, createCollection, addToCollection, removeFromCollection, deleteCollection,
    // 搜索
    doSearch,
  }
})
