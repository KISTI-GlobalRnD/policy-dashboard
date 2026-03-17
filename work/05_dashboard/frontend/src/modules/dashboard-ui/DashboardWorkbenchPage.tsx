import { useEffect, useMemo } from "react";
import { EmptyState } from "../../shared/ui/EmptyState";
import { useDashboardDataset } from "../dashboard-data/useDashboardDataset";
import { buildDashboardViewModel } from "../dashboard-model/dashboardSelectors";
import { useDashboardStore } from "../dashboard-model/dashboardStore";
import { readDashboardUrlState, writeDashboardUrlState } from "../dashboard-model/urlState";
import { DashboardHeader } from "./DashboardHeader";
import { EvidenceBoard } from "./EvidenceBoard";
import { FilterBar } from "./FilterBar";
import { OverviewBoard } from "./OverviewBoard";
import { PolicyRail } from "./PolicyRail";
import { TracePanel } from "./TracePanel";
import styles from "./DashboardWorkbenchPage.module.css";

export function DashboardWorkbenchPage() {
  const { data, error, isLoading } = useDashboardDataset();

  const {
    search,
    resourceCategoryId,
    strategyTermId,
    techDomainId,
    projectionStatus,
    rowLimit,
    activePolicyId,
    activeContentId,
    initializedFromUrl,
    hydrateFromUrl,
    markUrlInitialized,
    setSearch,
    setResourceCategoryId,
    setStrategyTermId,
    setTechDomainId,
    setProjectionStatus,
    setRowLimit,
    setActivePolicyId,
    setActiveContentId,
    resetFilters,
  } = useDashboardStore();

  const isResetDisabled =
    search.length === 0 &&
    resourceCategoryId === "all" &&
    strategyTermId === "all" &&
    techDomainId === "all" &&
    projectionStatus === "all" &&
    rowLimit === 12;

  useEffect(() => {
    if (initializedFromUrl) {
      return;
    }

    hydrateFromUrl(readDashboardUrlState());
    markUrlInitialized();
  }, [hydrateFromUrl, initializedFromUrl, markUrlInitialized]);

  const viewModel = useMemo(() => {
    if (!data) {
      return null;
    }

    return buildDashboardViewModel(data, {
      search,
      resourceCategoryId,
      strategyTermId,
      techDomainId,
      projectionStatus,
      rowLimit,
      activePolicyId,
      activeContentId,
    });
  }, [activeContentId, activePolicyId, data, projectionStatus, resourceCategoryId, rowLimit, search, strategyTermId, techDomainId]);

  useEffect(() => {
    if (!viewModel) {
      return;
    }

    if (strategyTermId !== viewModel.suggestedStrategyTermId) {
      setStrategyTermId(viewModel.suggestedStrategyTermId);
      return;
    }

    if (techDomainId !== viewModel.suggestedTechDomainId) {
      setTechDomainId(viewModel.suggestedTechDomainId);
      return;
    }

    if (projectionStatus !== viewModel.suggestedProjectionStatus) {
      setProjectionStatus(viewModel.suggestedProjectionStatus);
      return;
    }

    if (activePolicyId !== viewModel.suggestedActivePolicyId) {
      setActivePolicyId(viewModel.suggestedActivePolicyId);
      return;
    }

    if (resourceCategoryId !== viewModel.suggestedResourceCategoryId) {
      setResourceCategoryId(viewModel.suggestedResourceCategoryId);
      return;
    }

    if (activeContentId !== viewModel.suggestedActiveContentId) {
      setActiveContentId(viewModel.suggestedActiveContentId);
    }
  }, [
    activeContentId,
    activePolicyId,
    resourceCategoryId,
    setActiveContentId,
    setActivePolicyId,
    setProjectionStatus,
    setResourceCategoryId,
    setStrategyTermId,
    setTechDomainId,
    projectionStatus,
    strategyTermId,
    techDomainId,
    viewModel,
  ]);

  useEffect(() => {
    if (!initializedFromUrl || !viewModel) {
      return;
    }

    writeDashboardUrlState({
      search,
      resourceCategoryId: viewModel.suggestedResourceCategoryId,
      strategyTermId: viewModel.suggestedStrategyTermId,
      techDomainId: viewModel.suggestedTechDomainId,
      projectionStatus: viewModel.suggestedProjectionStatus,
      rowLimit,
      activePolicyId: viewModel.suggestedActivePolicyId,
      activeContentId: viewModel.suggestedActiveContentId,
    });
  }, [
    initializedFromUrl,
    resourceCategoryId,
    rowLimit,
    search,
    projectionStatus,
    strategyTermId,
    techDomainId,
    viewModel,
  ]);

  if (isLoading) {
    return (
      <main className={styles.shell}>
        <EmptyState
          eyebrow="Loading"
          title="대시보드 데이터를 불러오는 중"
          body="정책, 기술영역, 근거 데이터를 읽어 정책-기술 집중도를 구성하고 있습니다."
        />
      </main>
    );
  }

  if (error || !data || !viewModel) {
    return (
      <main className={styles.shell}>
        <EmptyState
          eyebrow="Load Error"
          title="데이터를 불러오지 못했습니다."
          body={error?.message ?? "정책·기술 데이터셋을 불러오지 못했습니다."}
        />
      </main>
    );
  }

  const hasFilter =
    Boolean(search) ||
    viewModel.suggestedStrategyTermId !== "all" ||
    viewModel.suggestedTechDomainId !== "all" ||
    viewModel.suggestedProjectionStatus !== "all";

  const dashboardLinks = (() => {
    const params = new URLSearchParams(window.location.search);
    params.set("view", "mapping");
    params.delete("board");
    const mappingWorkbenchHref = `${window.location.pathname}${params.toString() ? `?${params.toString()}` : ""}`;

    const networkParams = new URLSearchParams(params);
    networkParams.set("board", "network");
    const mappingNetworkHref = `${window.location.pathname}?${networkParams.toString()}`;

    const ontologyNetworkParams = new URLSearchParams(params);
    ontologyNetworkParams.set("view", "mapping");
    ontologyNetworkParams.set("board", "ontology-network");
    const ontologyNetworkHref = `${window.location.pathname}?${ontologyNetworkParams.toString()}`;

    return {
      mappingWorkbenchHref,
      mappingNetworkHref,
      ontologyNetworkHref,
    };
  })();

  return (
    <main className={styles.shell}>
      <DashboardHeader
        totalPolicies={data.stats.policy_count}
        totalGroups={data.stats.group_count}
        totalContents={data.stats.content_count}
        totalEvidence={data.stats.content_evidence_count}
        matchedContents={viewModel.matchedContentCount}
        activePolicyName={viewModel.activePolicyView?.policy.policy_name ?? null}
        packId={data.sample_scope.pack_id}
        mappingWorkbenchUrl={dashboardLinks.mappingWorkbenchHref}
        mappingNetworkUrl={dashboardLinks.mappingNetworkHref}
        mappingOntologyNetworkUrl={dashboardLinks.ontologyNetworkHref}
      />
      <FilterBar
        dataset={data}
        search={search}
        resourceCategoryId={viewModel.suggestedResourceCategoryId}
        strategyTermId={viewModel.suggestedStrategyTermId}
        techDomainId={viewModel.suggestedTechDomainId}
        projectionStatus={viewModel.suggestedProjectionStatus}
        rowLimit={rowLimit}
        strategyOptions={viewModel.availableStrategyOptions}
        techDomainOptions={viewModel.availableTechDomainOptions}
        strategyScopeContentCount={viewModel.strategyScopeContentCount}
        techDomainScopeContentCount={viewModel.techDomainScopeContentCount}
        projectionScopeContentCount={viewModel.projectionScopeContentCount}
        curatedProjectionContentCount={viewModel.curatedProjectionContentCount}
        provisionalProjectionContentCount={viewModel.provisionalProjectionContentCount}
        visiblePolicyCount={viewModel.visiblePolicyCount}
        matchedContentCount={viewModel.matchedContentCount}
        activePolicyName={viewModel.activePolicyView?.policy.policy_name ?? null}
        onSearchChange={setSearch}
        onResourceCategoryChange={setResourceCategoryId}
        onStrategyChange={setStrategyTermId}
        onTechDomainChange={setTechDomainId}
        onProjectionStatusChange={setProjectionStatus}
        onRowLimitChange={setRowLimit}
        onResetFilters={resetFilters}
        isResetDisabled={isResetDisabled}
      />
      <OverviewBoard
        dataset={data}
        overviewByCategory={viewModel.overviewByCategory}
        visiblePolicyCount={viewModel.visiblePolicyCount}
        matchedContentCount={viewModel.matchedContentCount}
        search={search}
        resourceCategoryId={viewModel.suggestedResourceCategoryId}
        strategyTermId={viewModel.suggestedStrategyTermId}
        techDomainId={viewModel.suggestedTechDomainId}
      />
      <section className={styles.workbench}>
        <PolicyRail
          policyViews={viewModel.policyViews}
          activePolicyId={viewModel.suggestedActivePolicyId}
          hasFilter={hasFilter}
          onSelectPolicy={setActivePolicyId}
        />
        <EvidenceBoard
          activePolicyView={viewModel.activePolicyView}
          activeRows={viewModel.activeRows}
          resourceCategoryId={viewModel.suggestedResourceCategoryId}
          activeContentId={viewModel.suggestedActiveContentId}
          onSelectCategory={setResourceCategoryId}
          onSelectContent={setActiveContentId}
        />
        <TracePanel activeTrace={viewModel.activeTrace} />
      </section>
    </main>
  );
}
