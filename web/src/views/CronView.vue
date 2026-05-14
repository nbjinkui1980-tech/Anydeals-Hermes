<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { Clock, Pause, Play, Plus, Trash2, Zap } from "lucide-vue-next";
import { NButton, NSelect, NTag } from "naive-ui";
import { api } from "@/lib/api";
import type { CronJob } from "@/lib/api";
import { useI18n } from "vue-i18n";
import { showToast } from "@/components/Toast";
import { useConfirmDelete } from "@/composables/useConfirmDelete";
import DeleteConfirmDialog from "@/components/DeleteConfirmDialog.vue";
import PluginSlot from "@/components/PluginSlot.vue";

const { t } = useI18n();

const DELIVER_OPTS = [
  { label: "Local", value: "local" },
  { label: "Telegram", value: "telegram" },
  { label: "Discord", value: "discord" },
  { label: "Slack", value: "slack" },
  { label: "Email", value: "email" },
];

const STATUS_VARIANT: Record<string, "success" | "warning" | "error"> = {
  enabled: "success",
  scheduled: "success",
  paused: "warning",
  error: "error",
  completed: "error",
};

const jobs = ref<CronJob[]>([]);
const loading = ref(true);

const prompt = ref("");
const schedule = ref("");
const name = ref("");
const deliver = ref("local");
const creating = ref(false);

function formatTime(iso?: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

async function loadJobs() {
  try {
    jobs.value = await api.getCronJobs();
  } catch {
    showToast({ message: t("common.loading"), type: "error" });
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadJobs();
});

async function handleCreate() {
  if (!prompt.value.trim() || !schedule.value.trim()) {
    showToast({
      message: `${t("cron.prompt")} & ${t("cron.schedule")} required`,
      type: "error",
    });
    return;
  }
  creating.value = true;
  try {
    await api.createCronJob({
      prompt: prompt.value.trim(),
      schedule: schedule.value.trim(),
      name: name.value.trim() || undefined,
      deliver: deliver.value,
    });
    showToast({ message: t("common.create") + " ✓", type: "success" });
    prompt.value = "";
    schedule.value = "";
    name.value = "";
    deliver.value = "local";
    loadJobs();
  } catch (e) {
    showToast({ message: `${t("config.failedToSave")}: ${e}`, type: "error" });
  } finally {
    creating.value = false;
  }
}

async function handlePauseResume(job: CronJob) {
  try {
    const isPaused = job.state === "paused";
    if (isPaused) {
      await api.resumeCronJob(job.id);
    } else {
      await api.pauseCronJob(job.id);
    }
    showToast({
      message: `${isPaused ? t("cron.resume") : t("cron.pause")}: "${job.name || job.prompt.slice(0, 30)}"`,
      type: "success",
    });
    loadJobs();
  } catch (e) {
    showToast({ message: `${t("status.error")}: ${e}`, type: "error" });
  }
}

async function handleTrigger(job: CronJob) {
  try {
    await api.triggerCronJob(job.id);
    showToast({
      message: `${t("cron.triggerNow")}: "${job.name || job.prompt.slice(0, 30)}"`,
      type: "success",
    });
    loadJobs();
  } catch (e) {
    showToast({ message: `${t("status.error")}: ${e}`, type: "error" });
  }
}

const jobDelete = useConfirmDelete(async (id: string) => {
  const job = jobs.value.find((j) => j.id === id);
  try {
    await api.deleteCronJob(id);
    showToast({
      message: `${t("common.delete")}: "${job?.name || (job?.prompt ?? "").slice(0, 30) || id}"`,
      type: "success",
    });
    loadJobs();
  } catch (e) {
    showToast({ message: `${t("status.error")}: ${e}`, type: "error" });
    throw e;
  }
});

const pendingJob = computed(() =>
  jobDelete.isOpen() ? jobs.value.find((j) => j.id === jobDelete.pendingId.value) : null
);

const deleteDescription = computed(() => {
  const pj = pendingJob.value;
  if (pj) {
    return `"${pj.name || pj.prompt.slice(0, 40)}" — ${t("cron.confirmDeleteMessage")}`;
  }
  return t("cron.confirmDeleteMessage");
});
</script>

<template>
  <div class="flex flex-col gap-6">
    <PluginSlot name="cron:top" />

    <DeleteConfirmDialog
      :open="jobDelete.isOpen()"
      :title="t('cron.confirmDeleteTitle')"
      :description="deleteDescription"
      :loading="jobDelete.isDeleting.value"
      destructive
      @confirm="jobDelete.confirm()"
      @cancel="jobDelete.cancel()"
    />

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-24">
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>

    <template v-else>
      <!-- Create new job form -->
      <div class="border border-border bg-card">
        <div class="px-4 py-3 border-b border-border flex items-center gap-2">
          <Plus class="h-4 w-4" />
          <span class="text-sm font-semibold tracking-wide">{{ t('cron.newJob') }}</span>
        </div>
        <div class="p-4">
          <div class="grid gap-4">
            <div class="grid gap-2">
              <span class="text-xs text-muted-foreground">{{ t('cron.nameOptional') }}</span>
              <NInput
                size="small"
                :placeholder="t('cron.namePlaceholder')"
                :value="name"
                @update:value="(v: string) => name = v"
              />
            </div>

            <div class="grid gap-2">
              <span class="text-xs text-muted-foreground">{{ t('cron.prompt') }}</span>
              <textarea
                class="flex min-h-[80px] w-full border border-border bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                :placeholder="t('cron.promptPlaceholder')"
                :value="prompt"
                @input="(e: Event) => prompt = (e.target as HTMLTextAreaElement).value"
              />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div class="grid gap-2">
                <span class="text-xs text-muted-foreground">{{ t('cron.schedule') }}</span>
                <NInput
                  size="small"
                  :placeholder="t('cron.schedulePlaceholder')"
                  :value="schedule"
                  @update:value="(v: string) => schedule = v"
                />
              </div>

              <div class="grid gap-2">
                <span class="text-xs text-muted-foreground">{{ t('cron.deliverTo') }}</span>
                <NSelect
                  size="small"
                  :value="deliver"
                  :options="DELIVER_OPTS"
                  @update:value="(v: string) => deliver = v"
                />
              </div>

              <div class="flex items-end">
                <NButton
                  :disabled="creating"
                  @click="handleCreate"
                  class="w-full"
                  size="small"
                >
                  <template #icon><Plus class="h-3 w-3" /></template>
                  {{ creating ? t('common.creating') : t('common.create') }}
                </NButton>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Jobs list -->
      <div class="flex flex-col gap-3">
        <div class="flex items-center gap-2 text-muted-foreground text-sm">
          <Clock class="h-4 w-4" />
          <span class="font-mondwest text-[0.65rem] tracking-[0.12em] uppercase">{{ t('cron.scheduledJobs') }} ({{ jobs.length }})</span>
        </div>

        <div
          v-if="jobs.length === 0"
          class="border border-border bg-card p-8 text-center text-sm text-muted-foreground"
        >
          {{ t('cron.noJobs') }}
        </div>

        <div
          v-for="job in jobs"
          :key="job.id"
          class="border border-border bg-card"
        >
          <div class="flex items-center gap-4 p-4">
            <!-- Info -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="font-medium text-sm truncate">
                  {{ job.name || job.prompt.slice(0, 60) + (job.prompt.length > 60 ? '...' : '') }}
                </span>
                <NTag
                  :type="STATUS_VARIANT[job.state] ?? 'default'"
                  size="small"
                  :bordered="false"
                >
                  {{ job.state }}
                </NTag>
                <NTag
                  v-if="job.deliver && job.deliver !== 'local'"
                  size="small"
                  :bordered="true"
                >
                  {{ job.deliver }}
                </NTag>
              </div>
              <p v-if="job.name" class="text-xs text-muted-foreground truncate mb-1">
                {{ job.prompt.slice(0, 100) }}{{ job.prompt.length > 100 ? '...' : '' }}
              </p>
              <div class="flex items-center gap-4 text-xs text-muted-foreground">
                <span class="font-mono">{{ job.schedule_display }}</span>
                <span>{{ t('cron.last') }}: {{ formatTime(job.last_run_at) }}</span>
                <span>{{ t('cron.next') }}: {{ formatTime(job.next_run_at) }}</span>
              </div>
              <p v-if="job.last_error" class="text-xs text-destructive mt-1">
                {{ job.last_error }}
              </p>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-1 shrink-0">
              <NButton
                text
                size="small"
                :title="job.state === 'paused' ? t('cron.resume') : t('cron.pause')"
                @click="handlePauseResume(job)"
              >
                <template #icon>
                  <Play v-if="job.state === 'paused'" class="h-4 w-4 text-success" />
                  <Pause v-else class="h-4 w-4 text-warning" />
                </template>
              </NButton>

              <NButton
                text
                size="small"
                :title="t('cron.triggerNow')"
                @click="handleTrigger(job)"
              >
                <template #icon><Zap class="h-4 w-4" /></template>
              </NButton>

              <NButton
                text
                size="small"
                :title="t('common.delete')"
                @click="jobDelete.requestDelete(job.id)"
              >
                <template #icon><Trash2 class="h-4 w-4 text-destructive" /></template>
              </NButton>
            </div>
          </div>
        </div>
      </div>
    </template>

    <PluginSlot name="cron:bottom" />
  </div>
</template>
