import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "../../shared/ui/EmptyState";
import { formatNumber } from "../../shared/lib/format";
import { useDashboardDataset } from "../dashboard-data/useDashboardDataset";
import { buildMappingWorkbenchViewModel } from "../dashboard-model/mappingWorkbenchSelectors";
import { readMappingUrlState, writeMappingUrlState } from "../dashboard-model/mappingUrlState";
import { useMappingWorkbenchStore } from "../dashboard-model/mappingWorkbenchStore";
import { CellInspectorPanel } from "./CellInspectorPanel";
import { EvidenceTraceDrawer } from "./EvidenceTraceDrawer";
import { MappingFilterBar } from "./MappingFilterBar";
import { MappingHeader } from "./MappingHeader";
import { PolicyLedgerPanel } from "./PolicyLedgerPanel";
import { PolicyTechMatrixBoard } from "./PolicyTechMatrixBoard";
import { PolicyTechNetworkMap } from "./PolicyTechNetworkMap";
import styles from "./MappingWorkbenchPage.module.css";

type MappingBoardMode = "matrix" | "network";

type MappingWorkbenchPageProps = {
  initialMode?: MappingBoardMode;
};

export function MappingWorkbenchPage({ initialMode = "matrix" }: MappingWorkbenchPageProps) {
  const { data, error, isLoading } = useDashboardDataset();
  const [isOverviewOpen, setOverviewOpen] = useState(false);
  const [isFilterOpen, setFilterOpen] = useState(false);
  const [boardMode, setBoardMode] = useState<MappingBoardMode>(initialMode);
  const {
    search,
    policyFilterId,
    resourceCategoryId,
    strategyTermId,
    techDomainFilterId,
    mappingStatus,
    reviewStatus,
    inspectorPolicyId,
    inspectorTechDomainId,
    activeContentId,
    initializedFromUrl,
    hydrateFromUrl,
    markUrlInitialized,
    setSearch,
    setPolicyFilterId,
    setResourceCategoryId,
    setStrategyTermId,
    setTechDomainFilterId,
    setMappingStatus,
    setReviewStatus,
    setInspectorPolicyId,
    setInspectorTechDomainId,
    selectCell,
    selectContent,
    resetFilters,
    clearInspector,
  } = useMappingWorkbenchStore();

  useEffect(() => {
    if (initializedFromUrl) {
      return;
    }

    hydrateFromUrl(readMappingUrlState());
    markUrlInitialized();
  }, [hydrateFromUrl, initializedFromUrl, markUrlInitialized]);

  const viewModel = useMemo(() => {
    if (!data) {
      return null;
    }

    return buildMappingWorkbenchViewModel(data, {
      search,
      policyFilterId,
      resourceCategoryId,
      strategyTermId,
      techDomainFilterId,
      mappingStatus,
      reviewStatus,
      inspectorPolicyId,
      inspectorTechDomainId,
      activeContentId,
    });
  }, [
    activeContentId,
    data,
    inspectorPolicyId,
    inspectorTechDomainId,
    mappingStatus,
    policyFilterId,
    resourceCategoryId,
    reviewStatus,
    search,
    strategyTermId,
    techDomainFilterId,
  ]);

  useEffect(() => {
    if (!viewModel) {
      return;
    }

    if (inspectorPolicyId !== viewModel.suggestedInspectorPolicyId) {
      setInspectorPolicyId(viewModel.suggestedInspectorPolicyId);
      return;
    }

    if (inspectorTechDomainId !== viewModel.suggestedInspectorTechDomainId) {
      setInspectorTechDomainId(viewModel.suggestedInspectorTechDomainId);
      return;
    }

    if (activeContentId !== viewModel.suggestedActiveContentId) {
      selectContent(viewModel.suggestedActiveContentId);
    }
  }, [
    activeContentId,
    inspectorPolicyId,
    inspectorTechDomainId,
    selectContent,
    setInspectorPolicyId,
    setInspectorTechDomainId,
    viewModel,
  ]);

  useEffect(() => {
    if (!initializedFromUrl || !viewModel) {
      return;
    }

    writeMappingUrlState({
      search,
      policyFilterId,
      resourceCategoryId,
      strategyTermId,
      techDomainFilterId,
      mappingStatus,
      reviewStatus,
      inspectorPolicyId: viewModel.suggestedInspectorPolicyId,
      inspectorTechDomainId: viewModel.suggestedInspectorTechDomainId,
      activeContentId: viewModel.suggestedActiveContentId,
    });
  }, [
    initializedFromUrl,
    mappingStatus,
    policyFilterId,
    resourceCategoryId,
    reviewStatus,
    search,
    strategyTermId,
    techDomainFilterId,
    viewModel,
  ]);

  const isResetDisabled =
    search.length === 0 &&
    policyFilterId === "all" &&
    resourceCategoryId === "all" &&
    strategyTermId === "all" &&
    techDomainFilterId === "all" &&
    mappingStatus === "all" &&
    reviewStatus === "all";

  const activeFilterCount = [
    search.length > 0,
    policyFilterId !== "all",
    resourceCategoryId !== "all",
    strategyTermId !== "all",
    techDomainFilterId !== "all",
    mappingStatus !== "all",
    reviewStatus !== "all",
  ].filter(Boolean).length;

  const handleSelectPolicySummary = (policyId: string | null) => {
    setInspectorPolicyId(policyId);
    setInspectorTechDomainId(null);
    selectContent(null);
  };

  const handleSelectDomainSummary = (domainId: string | null) => {
    setInspectorPolicyId(null);
    setInspectorTechDomainId(domainId);
    selectContent(null);
  };

  const syncBoardModeToUrl = (nextMode: MappingBoardMode) => {
    const params = new URLSearchParams(window.location.search);
    params.set("board", nextMode);

    if (nextMode === "matrix") {
      params.delete("board");
    }

    window.history.replaceState({}, "", `${window.location.pathname}${params.toString() ? `?${params.toString()}` : ""}`);
    setBoardMode(nextMode);
  };

  const dashboardUrl = (() => {
    const params = new URLSearchParams(window.location.search);
    params.delete("view");
    params.delete("board");
    const query = params.toString();
    return `${window.location.pathname}${query ? `?${query}` : ""}`;
  })();

  if (isLoading) {
    return (
      <main className={styles.shell}>
        <EmptyState
          eyebrow="Loading"
          title="매핑 워크벤치를 준비하는 중"
          body="정책과 기술 대분류 매트릭스를 만들기 위해 curated pack을 읽고 있습니다."
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
          body={error?.message ?? "curated content sample pack 로딩에 실패했습니다."}
        />
      </main>
    );
  }

  return (
    <main className={styles.shell}>
      <section className={styles.pageControls}>
        <div className={styles.pageControlsCopy}>
          <p className={styles.eyebrow}>Workbench Layout</p>
          <h1 className={styles.pageControlsTitle}>매트릭스를 먼저 보고, 설명과 필터는 필요할 때만 연다</h1>
          <p className={styles.sectionBody}>
            현재 범위는 정책 {formatNumber(viewModel.visiblePolicyCount)}개, 대표 내용 {formatNumber(viewModel.filteredRows.length)}개,
            활성 필터 {formatNumber(activeFilterCount)}개입니다.
          </p>
        </div>

        <div className={styles.pageControlsActions}>
          <button
            type="button"
            className={isOverviewOpen ? styles.pageControlButtonActive : styles.pageControlButton}
            onClick={() => setOverviewOpen((value) => !value)}
          >
            {isOverviewOpen ? "개요 접기" : "개요 보기"}
          </button>
          <button
            type="button"
            className={isFilterOpen ? styles.pageControlButtonActive : styles.pageControlButton}
            onClick={() => setFilterOpen((value) => !value)}
          >
            {isFilterOpen ? `필터 접기 (${formatNumber(activeFilterCount)})` : `필터 보기 (${formatNumber(activeFilterCount)})`}
          </button>
          <a href={dashboardUrl} className={styles.pageControlButton}>
            대시보드로 이동
          </a>
          <button
            type="button"
            className={boardMode === "matrix" ? styles.tabButtonActive : styles.tabButton}
            onClick={() => syncBoardModeToUrl("matrix")}
          >
            매트릭스
          </button>
          <button
            type="button"
            className={boardMode === "network" ? styles.tabButtonActive : styles.tabButton}
            onClick={() => syncBoardModeToUrl("network")}
          >
            네트워크
          </button>
        </div>
      </section>

      {isOverviewOpen ? (
        <MappingHeader
          packId={data.sample_scope.pack_id}
          generatedFrom={data.sample_scope.generated_from}
          totalPolicies={data.stats.policy_count}
          visiblePolicyCount={viewModel.visiblePolicyCount}
          mappedDomainCount={viewModel.mappedDomainCount}
          mappedGroupCount={viewModel.mappedGroupCount}
          mappedContentCount={viewModel.mappedContentCount}
          unmappedContentCount={viewModel.unmappedContentCount}
          reviewedContentCount={viewModel.reviewedContentCount}
        />
      ) : null}

      {isFilterOpen ? (
        <MappingFilterBar
          search={search}
          policyFilterId={policyFilterId}
          resourceCategoryId={resourceCategoryId}
          strategyTermId={strategyTermId}
          techDomainFilterId={techDomainFilterId}
          mappingStatus={mappingStatus}
          reviewStatus={reviewStatus}
          filteredContentCount={viewModel.filteredRows.length}
          visiblePolicyCount={viewModel.visiblePolicyCount}
          availablePolicies={viewModel.availablePolicies}
          availableStrategies={viewModel.availableStrategies}
          availableTechDomains={viewModel.availableTechDomains}
          availableReviewStatuses={viewModel.availableReviewStatuses}
          onSearchChange={setSearch}
          onPolicyFilterChange={setPolicyFilterId}
          onResourceCategoryChange={setResourceCategoryId}
          onStrategyChange={setStrategyTermId}
          onTechDomainFilterChange={setTechDomainFilterId}
          onMappingStatusChange={setMappingStatus}
          onReviewStatusChange={setReviewStatus}
          onReset={resetFilters}
          isResetDisabled={isResetDisabled}
        />
      ) : null}

      <section className={styles.workspace}>
        <div className={styles.primaryColumn}>
          <PolicyLedgerPanel
            rows={viewModel.matrixRows}
            selectedPolicyId={viewModel.suggestedInspectorPolicyId}
            onSelectPolicy={(policyId) => (policyId ? handleSelectPolicySummary(policyId) : clearInspector())}
          />

          {boardMode === "matrix" ? (
            <PolicyTechMatrixBoard
              rows={viewModel.matrixRows}
              domains={viewModel.matrixDomains}
              selectedPolicyId={viewModel.suggestedInspectorPolicyId}
              selectedDomainId={viewModel.suggestedInspectorTechDomainId}
              onSelectPolicy={(policyId) => (policyId ? handleSelectPolicySummary(policyId) : clearInspector())}
              onSelectDomain={(domainId) => (domainId ? handleSelectDomainSummary(domainId) : clearInspector())}
              onSelectCell={selectCell}
            />
          ) : (
            <PolicyTechNetworkMap
              rows={viewModel.matrixRows}
              domains={viewModel.matrixDomains}
              selectedPolicyId={viewModel.suggestedInspectorPolicyId}
              selectedDomainId={viewModel.suggestedInspectorTechDomainId}
              onSelectPolicy={(policyId) => (policyId ? handleSelectPolicySummary(policyId) : clearInspector())}
              onSelectDomain={(domainId) => (domainId ? handleSelectDomainSummary(domainId) : clearInspector())}
              onSelectCell={selectCell}
            />
          )}
        </div>

        <div className={styles.detailColumn}>
          <CellInspectorPanel
            selectedCell={viewModel.selectedCell}
            selectedPolicySummary={viewModel.selectedPolicySummary}
            selectedDomainSummary={viewModel.selectedDomainSummary}
            selectedCellGroups={viewModel.selectedCellGroups}
            selectedPolicyUnmappedContents={viewModel.selectedPolicyUnmappedContents}
            activeContentId={viewModel.suggestedActiveContentId}
            onOpenCell={selectCell}
            onSelectContent={selectContent}
          />

          {viewModel.activeTrace ? <EvidenceTraceDrawer activeTrace={viewModel.activeTrace} onClose={() => selectContent(null)} /> : null}
        </div>
      </section>
    </main>
  );
}
