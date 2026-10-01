<script setup>
defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  wide: { type: Boolean, default: false },
})
const emit = defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="admin-modal-backdrop" @click.self="emit('close')">
      <div class="admin-modal" :class="{ wide }" role="dialog" aria-modal="true">
        <header class="admin-modal-head">
          <h2>{{ title }}</h2>
          <button type="button" class="icon-btn" aria-label="Tutup" @click="emit('close')">×</button>
        </header>
        <div class="admin-modal-body">
          <slot />
        </div>
      </div>
    </div>
  </Teleport>
</template>
