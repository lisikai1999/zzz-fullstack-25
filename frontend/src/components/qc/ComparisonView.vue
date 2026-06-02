<template>
  <div class="comparison-view">
    <div
      v-for="(annotator, idx) in annotators"
      :key="annotator.user_id"
      class="comparison-panel"
    >
      <div class="comparison-header">
        <span class="comp-user" :style="{ color: colors[idx] }">{{ annotator.username }}</span>
        <span class="comp-count">{{ annotator.annotations.length }} annotations</span>
      </div>
      <AnnotationCanvas
        :image-width="image.width || 512"
        :image-height="image.height || 512"
        :annotations="annotator.annotations"
        :read-only="true"
      />
    </div>
  </div>
</template>

<script setup>
import AnnotationCanvas from '../canvas/AnnotationCanvas.vue'

defineProps({
  annotators: { type: Array, default: () => [] },
  image: { type: Object, default: () => ({}) },
})

const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
</script>

<style scoped>
.comparison-view {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 12px;
}

.comparison-panel {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.comparison-header {
  padding: 10px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
}

.comp-user {
  font-weight: 600;
  font-size: 14px;
}

.comp-count {
  font-size: 12px;
  color: #999;
}
</style>
