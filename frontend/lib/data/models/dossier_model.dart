class DossierModel {
  final String id;
  final String inputClaim;
  final String language;
  final String overallVerdict;
  final double overallConfidence;
  final OriginatingAccountModel? patientZero;
  final List<TimelineEventModel> timeline;
  final List<ClaimModel> claimsCorpus;
  final List<ClaimClusterModel> clusters;
  final AttributionReportModel? attribution;
  final VideoForensicsModel? videoForensics;
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
    this.clusters = const [],
    this.attribution,
    this.videoForensics,
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
      clusters: (json['clusters'] as List<dynamic>?)
              ?.map((e) => ClaimClusterModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      attribution: json['attribution'] != null ? AttributionReportModel.fromJson(json['attribution']) : null,
      videoForensics: json['video_forensics'] != null ? VideoForensicsModel.fromJson(json['video_forensics']) : null,
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

class ClaimClusterModel {
  final String clusterId;
  final String label;
  final int claimCount;
  final DateTime? earliestTimestamp;
  final String? patientZeroSource;
  final List<ClaimModel> claims;

  ClaimClusterModel({
    required this.clusterId,
    required this.label,
    this.claimCount = 0,
    this.earliestTimestamp,
    this.patientZeroSource,
    this.claims = const [],
  });

  factory ClaimClusterModel.fromJson(Map<String, dynamic> json) {
    return ClaimClusterModel(
      clusterId: json['cluster_id'] as String? ?? '',
      label: json['label'] as String? ?? 'Cluster',
      claimCount: json['claim_count'] as int? ?? 0,
      earliestTimestamp: json['earliest_timestamp'] != null ? DateTime.tryParse(json['earliest_timestamp'] as String) : null,
      patientZeroSource: json['patient_zero_source'] as String?,
      claims: (json['claims'] as List<dynamic>?)?.map((e) => ClaimModel.fromJson(e as Map<String, dynamic>)).toList() ?? [],
    );
  }
}

class AttributionReportModel {
  final List<DomainAttributionModel> domains;
  final CoordinationSignalModel? coordination;
  final String summary;

  AttributionReportModel({
    this.domains = const [],
    this.coordination,
    this.summary = '',
  });

  factory AttributionReportModel.fromJson(Map<String, dynamic> json) {
    return AttributionReportModel(
      domains: (json['domains'] as List<dynamic>?)
              ?.map((e) => DomainAttributionModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      coordination: json['coordination'] != null ? CoordinationSignalModel.fromJson(json['coordination']) : null,
      summary: json['summary'] as String? ?? '',
    );
  }
}

class DomainAttributionModel {
  final String domain;
  final DateTime? registrationDate;
  final int? domainAgeDays;
  final bool isFreshlyRegistered;
  final String? mbfcRating;
  final bool isIfcnSignatory;
  final String credibilityTier;

  DomainAttributionModel({
    required this.domain,
    this.registrationDate,
    this.domainAgeDays,
    this.isFreshlyRegistered = false,
    this.mbfcRating,
    this.isIfcnSignatory = false,
    this.credibilityTier = 'unverified',
  });

  factory DomainAttributionModel.fromJson(Map<String, dynamic> json) {
    return DomainAttributionModel(
      domain: json['domain'] as String? ?? '',
      registrationDate: json['registration_date'] != null ? DateTime.tryParse(json['registration_date'] as String) : null,
      domainAgeDays: json['domain_age_days'] as int?,
      isFreshlyRegistered: json['is_freshly_registered'] as bool? ?? false,
      mbfcRating: json['mbfc_rating'] as String?,
      isIfcnSignatory: json['is_ifcn_signatory'] as bool? ?? false,
      credibilityTier: json['credibility_tier'] as String? ?? 'unverified',
    );
  }
}

class CoordinationSignalModel {
  final bool detected;
  final double coordinationScore;
  final int accountCount;
  final int timeWindowMinutes;
  final String matchedPhrase;
  final String details;

  CoordinationSignalModel({
    this.detected = false,
    this.coordinationScore = 0.0,
    this.accountCount = 0,
    this.timeWindowMinutes = 0,
    this.matchedPhrase = '',
    this.details = '',
  });

  factory CoordinationSignalModel.fromJson(Map<String, dynamic> json) {
    return CoordinationSignalModel(
      detected: json['detected'] as bool? ?? false,
      coordinationScore: (json['coordination_score'] as num?)?.toDouble() ?? 0.0,
      accountCount: json['account_count'] as int? ?? 0,
      timeWindowMinutes: json['time_window_minutes'] as int? ?? 0,
      matchedPhrase: json['matched_phrase'] as String? ?? '',
      details: json['details'] as String? ?? '',
    );
  }
}

class VideoForensicsModel {
  final String? videoUrl;
  final String? channelName;
  final DateTime? publishedAt;
  final int? viewCount;
  final String? transcriptExcerpt;
  final bool isRecycledFootage;
  final double recyclingConfidence;
  final List<String> keyframeMatches;
  final String verdictNotes;

  VideoForensicsModel({
    this.videoUrl,
    this.channelName,
    this.publishedAt,
    this.viewCount,
    this.transcriptExcerpt,
    this.isRecycledFootage = false,
    this.recyclingConfidence = 0.0,
    this.keyframeMatches = const [],
    this.verdictNotes = '',
  });

  factory VideoForensicsModel.fromJson(Map<String, dynamic> json) {
    return VideoForensicsModel(
      videoUrl: json['video_url'] as String?,
      channelName: json['channel_name'] as String?,
      publishedAt: json['published_at'] != null ? DateTime.tryParse(json['published_at'] as String) : null,
      viewCount: json['view_count'] as int?,
      transcriptExcerpt: json['transcript_excerpt'] as String?,
      isRecycledFootage: json['is_recycled_footage'] as bool? ?? false,
      recyclingConfidence: (json['recycling_confidence'] as num?)?.toDouble() ?? 0.0,
      keyframeMatches: (json['keyframe_matches'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      verdictNotes: json['verdict_notes'] as String? ?? '',
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
