class DossierModel {
  final String id;

  final String inputClaim;
  final String language;
  final String overallVerdict;
  final double overallConfidence;
  final OriginatingAccountModel? patientZero;
  final List<TimelineEventModel> timeline;
  final List<ClaimModel> claimsCorpus;
  final List<SubClaimModel> subClaims;
  final NarrativeProfileModel? narrative;
  final RedTeamAuditModel? redTeamAudit;
  final DateTime? generatedAt;

  DossierModel({
    required this.id,
    required this.inputClaim,
    this.language = 'en',
    required this.overallVerdict,
    required this.overallConfidence,
    this.patientZero,
    this.timeline = const [],
    this.claimsCorpus = const [],
    this.subClaims = const [],
    this.narrative,
    this.redTeamAudit,
    this.generatedAt,
  });

  factory DossierModel.fromJson(Map<String, dynamic> json) {
    return DossierModel(
      id: json['id'] as String? ?? '',
      inputClaim: json['input_claim'] as String? ?? '',
      language: json['language'] as String? ?? 'en',
      overallVerdict: json['overall_verdict'] as String? ?? json['verdict'] as String? ?? 'unverified',
      overallConfidence: (json['overall_confidence'] as num?)?.toDouble() ?? 
                         ((json['credibility_score'] as num?)?.toDouble() != null ? (json['credibility_score'] as num).toDouble() / 100.0 : 0.50),
      patientZero: json['patient_zero'] != null ? OriginatingAccountModel.fromJson(json['patient_zero']) : null,
      timeline: (json['timeline'] as List<dynamic>?)
              ?.map((e) => TimelineEventModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      claimsCorpus: (json['claims_corpus'] as List<dynamic>?)
              ?.map((e) => ClaimModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      subClaims: (json['sub_claims'] as List<dynamic>?)
              ?.map((e) => SubClaimModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      narrative: json['narrative'] != null ? NarrativeProfileModel.fromJson(json['narrative']) : null,
      redTeamAudit: json['red_team_audit'] != null ? RedTeamAuditModel.fromJson(json['red_team_audit']) : null,
      generatedAt: json['generated_at'] != null ? DateTime.tryParse(json['generated_at'] as String) : null,
    );
  }
}

class TimelineEventModel {
  final String id;
  final String source;
  final DateTime? timestamp;
  final String? url;
  final String? title;
  final String? snippet;
  final DateTime? earliestCdxTimestamp;
  final bool isPatientZeroCandidate;
  final String? clusterId;
  final String credibilityTier;

  TimelineEventModel({
    required this.id,
    required this.source,
    this.timestamp,
    this.url,
    this.title,
    this.snippet,
    this.earliestCdxTimestamp,
    this.isPatientZeroCandidate = false,
    this.clusterId,
    this.credibilityTier = 'unverified',
  });

  factory TimelineEventModel.fromJson(Map<String, dynamic> json) {
    return TimelineEventModel(
      id: json['id'] as String? ?? '',
      source: json['source'] as String? ?? 'Web Source',
      timestamp: json['timestamp'] != null ? DateTime.tryParse(json['timestamp'] as String) : null,
      url: json['url'] as String?,
      title: json['title'] as String? ?? json['event'] as String?,
      snippet: json['snippet'] as String?,
      earliestCdxTimestamp: json['earliest_cdx_timestamp'] != null 
          ? DateTime.tryParse(json['earliest_cdx_timestamp'] as String) 
          : null,
      isPatientZeroCandidate: json['is_patient_zero_candidate'] as bool? ?? false,
      clusterId: json['cluster_id'] as String?,
      credibilityTier: json['credibility_tier'] as String? ?? 'unverified',
    );
  }
}

class OriginatingAccountModel {
  final String platform;
  final String handle;
  final DateTime? firstSeenAt;
  final int? followerCount;
  final int priorFlaggedClaims;
  final int? accountAgeDays;
  final double? coordinationScore;

  OriginatingAccountModel({
    required this.platform,
    required this.handle,
    this.firstSeenAt,
    this.followerCount,
    this.priorFlaggedClaims = 0,
    this.accountAgeDays,
    this.coordinationScore,
  });

  factory OriginatingAccountModel.fromJson(Map<String, dynamic> json) {
    return OriginatingAccountModel(
      platform: json['platform'] as String? ?? 'unknown',
      handle: json['handle'] as String? ?? 'unknown',
      firstSeenAt: json['first_seen_at'] != null ? DateTime.tryParse(json['first_seen_at'] as String) : null,
      followerCount: json['follower_count'] as int?,
      priorFlaggedClaims: json['prior_flagged_claims'] as int? ?? 0,
      accountAgeDays: json['account_age_days'] as int?,
      coordinationScore: (json['coordination_score'] as num?)?.toDouble(),
    );
  }
}

class ClaimModel {
  final String id;
  final String text;
  final List<String> extractedEntities;
  final String? sourceUrl;
  final DateTime? timestamp;
  final String? clusterId;
  final String? sourcePlatform;
  final double? credibilityScore;

  ClaimModel({
    required this.id,
    required this.text,
    this.extractedEntities = const [],
    this.sourceUrl,
    this.timestamp,
    this.clusterId,
    this.sourcePlatform,
    this.credibilityScore,
  });

  factory ClaimModel.fromJson(Map<String, dynamic> json) {
    return ClaimModel(
      id: json['id'] as String? ?? '',
      text: json['text'] as String? ?? '',
      extractedEntities: (json['extracted_entities'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      sourceUrl: json['source_url'] as String?,
      timestamp: json['timestamp'] != null ? DateTime.tryParse(json['timestamp'] as String) : null,
      clusterId: json['cluster_id'] as String?,
      sourcePlatform: json['source_platform'] as String?,
      credibilityScore: (json['credibility_score'] as num?)?.toDouble(),
    );
  }
}

class SubClaimModel {
  final String id;
  final String text;
  final bool atomic;
  final String verdict;
  final double verdictConfidence;
  final List<EvidenceModel> evidence;

  SubClaimModel({
    required this.id,
    required this.text,
    this.atomic = true,
    required this.verdict,
    required this.verdictConfidence,
    this.evidence = const [],
  });

  factory SubClaimModel.fromJson(Map<String, dynamic> json) {
    return SubClaimModel(
      id: json['id'] as String? ?? '',
      text: json['text'] as String? ?? '',
      atomic: json['atomic'] as bool? ?? true,
      verdict: json['verdict'] as String? ?? 'unverified',
      verdictConfidence: (json['verdict_confidence'] as num?)?.toDouble() ?? 0.5,
      evidence: (json['evidence'] as List<dynamic>?)
              ?.map((e) => EvidenceModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

class EvidenceModel {
  final String id;
  final String excerpt;
  final String retrievedVia;
  final double confidence;
  final SourceModel? source;

  EvidenceModel({
    required this.id,
    required this.excerpt,
    required this.retrievedVia,
    required this.confidence,
    this.source,
  });

  factory EvidenceModel.fromJson(Map<String, dynamic> json) {
    return EvidenceModel(
      id: json['id'] as String? ?? '',
      excerpt: json['excerpt'] as String? ?? '',
      retrievedVia: json['retrieved_via'] as String? ?? 'unknown',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.5,
      source: json['source'] != null ? SourceModel.fromJson(json['source']) : null,
    );
  }
}

class SourceModel {
  final String id;
  final String url;
  final String domain;
  final String? snapshotUrl;
  final String credibilityTier;

  SourceModel({
    required this.id,
    required this.url,
    required this.domain,
    this.snapshotUrl,
    this.credibilityTier = 'unverified',
  });

  factory SourceModel.fromJson(Map<String, dynamic> json) {
    return SourceModel(
      id: json['id'] as String? ?? '',
      url: json['url'] as String? ?? '',
      domain: json['domain'] as String? ?? '',
      snapshotUrl: json['snapshot_url'] as String?,
      credibilityTier: json['credibility_tier'] as String? ?? 'unverified',
    );
  }
}

class NarrativeProfileModel {
  final String coreNarrative;
  final List<String> emotionalHooks;
  final String targetDemographic;
  final String plausibleIntent;
  final String? coordinatedClusterId;

  NarrativeProfileModel({
    required this.coreNarrative,
    this.emotionalHooks = const [],
    required this.targetDemographic,
    required this.plausibleIntent,
    this.coordinatedClusterId,
  });

  factory NarrativeProfileModel.fromJson(Map<String, dynamic> json) {
    return NarrativeProfileModel(
      coreNarrative: json['core_narrative'] as String? ?? '',
      emotionalHooks: (json['emotional_hooks'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      targetDemographic: json['target_demographic'] as String? ?? 'General Public',
      plausibleIntent: json['plausible_intent'] as String? ?? 'Virality',
      coordinatedClusterId: json['coordinated_cluster_id'] as String?,
    );
  }
}

class RedTeamAuditModel {
  final List<String> flags;
  final List<String> sourceCredibilityConcerns;
  final double confidenceAdjustment;

  RedTeamAuditModel({
    this.flags = const [],
    this.sourceCredibilityConcerns = const [],
    this.confidenceAdjustment = 0.0,
  });

  factory RedTeamAuditModel.fromJson(Map<String, dynamic> json) {
    return RedTeamAuditModel(
      flags: (json['flags'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      sourceCredibilityConcerns: (json['source_credibility_concerns'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      confidenceAdjustment: (json['confidence_adjustment'] as num?)?.toDouble() ?? 0.0,
    );
  }
}
