<template>
  <img v-if="theme.themeInfo?.loginLogo" :src="fileURL" alt="" height="45px" class="mr-8" />
  <template v-else>
    <div class="logo-text" :style="{ height }">
      <span class="logo-g" :class="!isDefaultTheme ? 'custom-logo-color-text' : ''">G</span><span class="logo-code" :class="!isDefaultTheme ? 'custom-logo-color-text' : ''">Code</span>
    </div>
  </template>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import useStore from '@/stores'
defineOptions({ name: 'LogoFull' })

defineProps({
  height: {
    type: String,
    default: '36px',
  },
})
const { theme } = useStore()
const isDefaultTheme = computed(() => {
  return theme.isDefaultTheme()
})

const fileURL = computed(() => {
  if (theme.themeInfo) {
    if (typeof theme.themeInfo?.loginLogo === 'string') {
      return theme.themeInfo?.loginLogo
    } else {
      return URL.createObjectURL(theme.themeInfo?.loginLogo)
    }
  } else {
    return ''
  }
})
</script>
<style lang="scss" scoped>
.logo-text {
  display: flex;
  align-items: center;
  line-height: 1;
  user-select: none;

  span {
    font-family: 'Arial Rounded MT Bold', 'Rounded Mplus 1p Bold', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -1px;
    border-radius: 8px;
  }

  .logo-g {
    color: var(--el-color-primary);
  }

  .logo-code {
    color: var(--el-text-color-primary);
  }
}

.custom-logo-color-text {
  color: var(--el-color-primary);
}
</style>
