<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <div class="admin-page-header">
    <div>
      <h1 class="admin-page-title">{{ title }}</h1>
      <p v-if="subtitle" class="muted hero-sub">{{ subtitle }}</p>
    </div>
    <div class="admin-page-actions">
      <slot name="actions" />
    </div>
  </div>
</template>
