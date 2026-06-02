<template>
  <div class="metrics-panel" v-if="results && results.length > 0">
    <h4>一致性指标</h4>
    <div class="metrics-grid">
      <div v-for="r in results" :key="r.id" class="metric-card" :class="{ flagged: r.flagged }">
        <div class="metric-type">{{ r.metric_type.toUpperCase() }}</div>
        <div class="metric-score" :class="scoreClass(r.score)">
          {{ r.score.toFixed(4) }}
        </div>
        <div class="metric-pair">
          标注 #{{ r.annotation_id_a }} vs #{{ r.annotation_id_b }}
        </div>
        <div v-if="r.flagged" class="flagged-badge">⚠ 低一致性</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  results: { type: Array, default: () => [] },
})

function scoreClass(score) {
  if (score >= 0.8) return 'excellent'
  if (score >= 0.7) return 'good'
  if (score >= 0.5) return 'moderate'
  return 'poor'
}
</script>

<style scoped>
.metrics-panel {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.metrics-panel h4 {
  font-size: 14px;
  color: #333;
  margin-bottom: 12px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}

.metric-card {
  padding: 12px;
  border-radius: 6px;
  background: #f9f9f9;
  border: 1px solid #eee;
  text-align: center;
}

.metric-card.flagged {
  background: #fff5f5;
  border-color: #ffcdd2;
}

.metric-type {
  font-size: 11px;
  font-weight: 600;
  color: #888;
  margin-bottom: 4px;
  letter-spacing: 0.5px;
}

.metric-score {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
}

.metric-score.excellent { color: #27ae60; }
.metric-score.good { color: #2ecc71; }
.metric-score.moderate { color: #f39c12; }
.metric-score.poor { color: #e74c3c; }

.metric-pair {
  font-size: 11px;
  color: #999;
}

.flagged-badge {
  margin-top: 6px;
  font-size: 11px;
  color: #e74c3c;
  font-weight: 500;
}
</style>
