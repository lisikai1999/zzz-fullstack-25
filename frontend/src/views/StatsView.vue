<template>
  <div class="stats-view">
    <h2>统计面板</h2>

    <div class="stats-grid" v-if="overview">
      <div class="stat-card">
        <div class="stat-value">{{ overview.total_images }}</div>
        <div class="stat-label">总影像数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ overview.total_tasks }}</div>
        <div class="stat-label">总任务数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ overview.completed_tasks }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ overview.pending_tasks }}</div>
        <div class="stat-label">待处理</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-value">{{ overview.flagged_items }}</div>
        <div class="stat-label">待仲裁</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ overview.total_annotators }}</div>
        <div class="stat-label">标注员</div>
      </div>
    </div>

    <div class="progress-section">
      <h3>完成进度</h3>
      <div class="progress-bar-wrapper" v-if="overview && overview.total_tasks > 0">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <span class="progress-text">{{ progressPercent.toFixed(1) }}%</span>
      </div>
      <p v-else class="no-data">暂无任务数据</p>
    </div>

    <div class="annotator-section">
      <h3>标注员统计</h3>
      <p v-if="loading" class="loading-text">加载中...</p>
      <div v-else-if="annotatorStats.length > 0" class="annotator-table">
        <div class="table-header">
          <span>标注员</span>
          <span>总任务</span>
          <span>已完成</span>
          <span>完成率</span>
          <span>平均一致性</span>
          <span>金标准偏差</span>
        </div>
        <div v-for="s in annotatorStats" :key="s.user_id" class="table-row">
          <span class="annotator-name">{{ s.username }}</span>
          <span>{{ s.total_tasks }}</span>
          <span>{{ s.completed_tasks }}</span>
          <span>{{ s.total_tasks > 0 ? ((s.completed_tasks / s.total_tasks) * 100).toFixed(0) + '%' : '-' }}</span>
          <span :class="consistencyClass(s.avg_consistency_score)">
            {{ s.avg_consistency_score !== null && s.avg_consistency_score !== undefined
               ? s.avg_consistency_score.toFixed(3) : '-' }}
          </span>
          <span :class="deviationClass(s.gold_standard_deviation)">
            {{ formatDeviation(s.gold_standard_deviation) }}
          </span>
        </div>
      </div>
      <p v-else class="no-data">暂无标注员数据</p>
    </div>

    <!-- Gold standard detail section -->
    <div class="gold-section" v-if="annotatorStats.some(s => s.gold_detail && s.gold_detail.count > 0)">
      <h3>金标准对比详情</h3>
      <div class="gold-grid">
        <div
          v-for="s in annotatorStats.filter(s => s.gold_detail && s.gold_detail.count > 0)"
          :key="'gold-' + s.user_id"
          class="gold-card"
        >
          <div class="gold-card-header">{{ s.username }}</div>
          <div class="gold-metrics">
            <div class="gold-metric">
              <span class="gold-metric-label">平均 IoU</span>
              <span class="gold-metric-value" :class="goldScoreClass(s.gold_detail.avg_iou)">
                {{ s.gold_detail.avg_iou.toFixed(4) }}
              </span>
            </div>
            <div class="gold-metric">
              <span class="gold-metric-label">平均 Dice</span>
              <span class="gold-metric-value" :class="goldScoreClass(s.gold_detail.avg_dice)">
                {{ s.gold_detail.avg_dice.toFixed(4) }}
              </span>
            </div>
            <div class="gold-metric">
              <span class="gold-metric-label">对比样本数</span>
              <span class="gold-metric-value">{{ s.gold_detail.count }}</span>
            </div>
          </div>
          <div class="gold-deviation-bar">
            <div class="deviation-label">偏差: {{ formatDeviation(s.gold_standard_deviation) }}</div>
            <div class="deviation-bar">
              <div
                class="deviation-fill"
                :class="deviationClass(s.gold_standard_deviation)"
                :style="{ width: Math.min((s.gold_standard_deviation || 0) * 100, 100) + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'

const overview = ref(null)
const annotatorStats = ref([])
const loading = ref(false)

const progressPercent = computed(() => {
  if (!overview.value || overview.value.total_tasks === 0) return 0
  return (overview.value.completed_tasks / overview.value.total_tasks) * 100
})

function consistencyClass(score) {
  if (score === null || score === undefined) return ''
  if (score >= 0.8) return 'score-good'
  if (score >= 0.6) return 'score-moderate'
  return 'score-poor'
}

function deviationClass(dev) {
  if (dev === null || dev === undefined) return ''
  if (dev <= 0.1) return 'deviation-excellent'
  if (dev <= 0.2) return 'deviation-good'
  if (dev <= 0.35) return 'deviation-moderate'
  return 'deviation-poor'
}

function goldScoreClass(score) {
  if (score >= 0.8) return 'score-good'
  if (score >= 0.6) return 'score-moderate'
  return 'score-poor'
}

function formatDeviation(dev) {
  if (dev === null || dev === undefined) return '无金标准'
  return dev.toFixed(3)
}

async function loadStats() {
  loading.value = true
  try {
    const resp = await api.getOverview()
    overview.value = resp.data
  } catch (e) {
    console.error(e)
  }

  // Dynamically fetch all annotators
  try {
    const annotatorsResp = await api.getAnnotators()
    const annotators = annotatorsResp.data

    const stats = []
    for (const annotator of annotators) {
      try {
        const resp = await api.getAnnotatorStats(annotator.id)
        stats.push(resp.data)
      } catch (e) {
        // annotator stats might fail if user has no activity
        stats.push({
          user_id: annotator.id,
          username: annotator.username,
          total_tasks: 0,
          completed_tasks: 0,
          avg_consistency_score: null,
          gold_standard_deviation: null,
          gold_detail: { avg_iou: null, avg_dice: null, count: 0 },
        })
      }
    }
    annotatorStats.value = stats
  } catch (e) {
    console.error('Failed to fetch annotators:', e)
  }
  loading.value = false
}

onMounted(loadStats)
</script>

<style scoped>
.stats-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-view h2 {
  font-size: 20px;
  color: #1a1a2e;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.stat-card.warning {
  border-left: 3px solid #e74c3c;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a2e;
}

.stat-label {
  font-size: 13px;
  color: #888;
  margin-top: 4px;
}

.progress-section, .annotator-section, .gold-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.progress-section h3, .annotator-section h3, .gold-section h3 {
  font-size: 16px;
  margin-bottom: 14px;
  color: #333;
}

.progress-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  flex: 1;
  height: 12px;
  background: #e8e8e8;
  border-radius: 6px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #27ae60, #2ecc71);
  border-radius: 6px;
  transition: width 0.5s ease;
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
  color: #27ae60;
  min-width: 50px;
}

.annotator-table {
  border: 1px solid #eee;
  border-radius: 6px;
  overflow: hidden;
}

.table-header, .table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1.5fr 1.5fr;
  padding: 10px 14px;
  font-size: 13px;
}

.table-header {
  background: #f8f9fa;
  font-weight: 600;
  color: #555;
  border-bottom: 1px solid #eee;
}

.table-row {
  border-bottom: 1px solid #f5f5f5;
}

.table-row:last-child {
  border-bottom: none;
}

.annotator-name {
  font-weight: 500;
}

.score-good { color: #27ae60; font-weight: 600; }
.score-moderate { color: #f39c12; font-weight: 600; }
.score-poor { color: #e74c3c; font-weight: 600; }

.deviation-excellent { color: #27ae60; font-weight: 600; }
.deviation-good { color: #2ecc71; font-weight: 600; }
.deviation-moderate { color: #f39c12; font-weight: 600; }
.deviation-poor { color: #e74c3c; font-weight: 600; }

.no-data, .loading-text {
  font-size: 13px;
  color: #999;
  text-align: center;
  padding: 16px 0;
}

/* Gold standard detail */
.gold-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.gold-card {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
}

.gold-card-header {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 12px;
  color: #333;
}

.gold-metrics {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.gold-metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.gold-metric-label {
  font-size: 11px;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.gold-metric-value {
  font-size: 18px;
  font-weight: 700;
}

.gold-deviation-bar {
  padding-top: 8px;
  border-top: 1px solid #eee;
}

.deviation-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.deviation-bar {
  height: 6px;
  background: #e8e8e8;
  border-radius: 3px;
  overflow: hidden;
}

.deviation-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}

.deviation-fill.deviation-excellent { background: #27ae60; }
.deviation-fill.deviation-good { background: #2ecc71; }
.deviation-fill.deviation-moderate { background: #f39c12; }
.deviation-fill.deviation-poor { background: #e74c3c; }
</style>
