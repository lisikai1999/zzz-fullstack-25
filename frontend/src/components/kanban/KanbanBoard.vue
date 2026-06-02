<template>
  <KanbanColumn
    v-for="col in columns"
    :key="col.key"
    :title="col.title"
    :tasks="tasks[col.key] || []"
    :color="col.color"
  />
</template>

<script setup>
import KanbanColumn from './KanbanColumn.vue'

defineProps({
  tasks: { type: Object, default: () => ({}) },
  columns: { type: Array, default: () => [] },
})
</script>
