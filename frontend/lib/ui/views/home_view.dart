import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../view_models/dossier_view_model.dart';
import '../../data/models/dossier_model.dart';

class HomeView extends StatefulWidget {
  const HomeView({super.key});

  @override
  State<HomeView> createState() => _HomeViewState();
}

class _HomeViewState extends State<HomeView> {
  late final DossierViewModel _viewModel;

  @override
  void initState() {
    super.initState();
    _viewModel = DossierViewModel();
  }

  @override
  void dispose() {
    _viewModel.dispose();
    super.dispose();
  }

  Future<void> _launchUrl(String? urlStr) async {
    if (urlStr == null || urlStr.isEmpty) return;
    final uri = Uri.tryParse(urlStr);
    if (uri != null && await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  void _showSettingsDialog() {
    final controller = TextEditingController(text: _viewModel.backendUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.settings, color: Colors.blueAccent),
            SizedBox(width: 8),
            Text('Backend Configuration'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Set the TruthTrace backend API endpoint:',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                labelText: 'API Base URL',
                hintText: 'http://localhost:8000 or http://10.0.2.2:8000',
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Tip: Use http://10.0.2.2:8000 for Android Emulator.',
              style: TextStyle(fontSize: 11, color: Colors.grey),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              if (controller.text.trim().isNotEmpty) {
                _viewModel.backendUrl = controller.text.trim();
              }
              Navigator.pop(ctx);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.shield_outlined, size: 20, color: Colors.blueAccent),
            ),
            const SizedBox(width: 10),
            const Text(
              'TruthTrace',
              style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: -0.5),
            ),
          ],
        ),
        centerTitle: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'Backend Settings',
            onPressed: _showSettingsDialog,
          ),
        ],
      ),
      body: ListenableBuilder(
        listenable: _viewModel,
        builder: (context, _) {
          return Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 860),
              child: ListView(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
                children: [
                  _buildInputCard(),
                  if (_viewModel.errorMessage != null) ...[
                    const SizedBox(height: 16),
                    _buildErrorCard(_viewModel.errorMessage!),
                  ],
                  if (_viewModel.dossier != null) ...[
                    const SizedBox(height: 24),
                    _buildDossierSection(_viewModel.dossier!),
                  ],
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildInputCard() {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Theme.of(context).dividerColor.withValues(alpha: 0.2)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Investigate a Claim',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            Text(
              'Enter any viral statement, headline, or URL to trace origins and verify evidence.',
              style: TextStyle(fontSize: 13, color: Theme.of(context).textTheme.bodySmall?.color),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _viewModel.claimController,
              maxLines: 3,
              decoration: InputDecoration(
                labelText: 'Claim / Assertion',
                hintText: 'e.g. Drinking salt water cures biological aging...',
                alignLabelWithHint: true,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                filled: true,
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _viewModel.urlController,
              decoration: InputDecoration(
                labelText: 'Or Article / Post URL',
                hintText: 'https://example.com/news-article',
                prefixIcon: const Icon(Icons.link, size: 20),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                filled: true,
              ),
            ),
            const SizedBox(height: 14),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                const Text('Try samples:', style: TextStyle(fontSize: 11, color: Colors.grey)),
                for (int i = 0; i < _viewModel.sampleClaims.length; i++)
                  ActionChip(
                    label: Text(
                      'Sample ${i + 1}',
                      style: const TextStyle(fontSize: 11),
                    ),
                    onPressed: () => _viewModel.selectSample(_viewModel.sampleClaims[i]),
                  ),
              ],
            ),
            const SizedBox(height: 18),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: FilledButton.icon(
                onPressed: _viewModel.isLoading ? null : _viewModel.analyze,
                icon: _viewModel.isLoading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.radar),
                label: Text(
                  _viewModel.isLoading ? 'Forensic Agents Investigating...' : 'Analyze Claim',
                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorCard(String message) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.red.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.red.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: Colors.red, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(color: Colors.red, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDossierSection(DossierModel dossier) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Forensic Dossier',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            IconButton.filledTonal(
              icon: const Icon(Icons.share_outlined, size: 18),
              tooltip: 'Share Dossier',
              onPressed: _viewModel.shareDossier,
            ),
          ],
        ),
        const SizedBox(height: 12),

        // Verdict & Confidence Card
        Card(
          elevation: 0,
          color: _getVerdictColor(dossier.overallVerdict).withValues(alpha: isDark ? 0.15 : 0.08),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: BorderSide(color: _getVerdictColor(dossier.overallVerdict).withValues(alpha: 0.3)),
          ),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                      decoration: BoxDecoration(
                        color: _getVerdictColor(dossier.overallVerdict),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        dossier.overallVerdict.toUpperCase(),
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ),
                    Text(
                      'Confidence: ${(dossier.overallConfidence * 100).toStringAsFixed(1)}%',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  dossier.inputClaim,
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
                if (dossier.id.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  Text(
                    'Dossier ID: ${dossier.id}',
                    style: TextStyle(fontSize: 11, color: Colors.grey.shade600, fontFamily: 'monospace'),
                  ),
                ],
              ],
            ),
          ),
        ),

        // Patient Zero Candidate Card
        if (dossier.patientZero != null) ...[
          const SizedBox(height: 16),
          Card(
            elevation: 0,
            color: Colors.amber.withValues(alpha: isDark ? 0.15 : 0.08),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(color: Colors.amber.withValues(alpha: 0.4)),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Text('🎯 ', style: TextStyle(fontSize: 18)),
                      Text(
                        'Patient Zero Candidate',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(
                        child: _buildMetaColumn('Platform', dossier.patientZero!.platform),
                      ),
                      Expanded(
                        child: _buildMetaColumn('Handle / Domain', '@${dossier.patientZero!.handle}'),
                      ),
                      Expanded(
                        child: _buildMetaColumn(
                          'First Indexed',
                          dossier.patientZero!.firstSeenAt != null
                              ? DateFormat('yyyy-MM-dd').format(dossier.patientZero!.firstSeenAt!)
                              : 'Earliest',
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],

        // Provenance Timeline
        if (dossier.timeline.isNotEmpty) ...[
          const SizedBox(height: 24),
          const Text(
            'Ascending Provenance Timeline',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: dossier.timeline.length,
            itemBuilder: (context, idx) {
              final ev = dossier.timeline[idx];
              final isLast = idx == dossier.timeline.length - 1;
              return _buildTimelineItem(ev, isLast);
            },
          ),
        ],

        // Narrative Profile
        if (dossier.narrative != null && dossier.narrative!.coreNarrative.isNotEmpty) ...[
          const SizedBox(height: 24),
          const Text(
            'Narrative Profile',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 10),
          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: BorderSide(color: Theme.of(context).dividerColor.withValues(alpha: 0.2)),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildProfileRow('Core Narrative', dossier.narrative!.coreNarrative),
                  const SizedBox(height: 8),
                  _buildProfileRow('Target Demographic', dossier.narrative!.targetDemographic),
                  if (dossier.narrative!.plausibleIntent.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    _buildProfileRow('Plausible Intent', dossier.narrative!.plausibleIntent),
                  ],
                ],
              ),
            ),
          ),
        ],

        // Action buttons
        const SizedBox(height: 24),
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: _viewModel.shareDossier,
                icon: const Icon(Icons.share, size: 18),
                label: const Text('Share Dossier'),
              ),
            ),
            const SizedBox(width: 12),
            OutlinedButton.icon(
              onPressed: _viewModel.clear,
              icon: const Icon(Icons.refresh, size: 18),
              label: const Text('New Analysis'),
            ),
          ],
        ),
        const SizedBox(height: 40),
      ],
    );
  }

  Widget _buildTimelineItem(TimelineEventModel ev, bool isLast) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Vertical line with dot
          Column(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: ev.isPatientZeroCandidate ? Colors.redAccent : Colors.blueAccent,
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white, width: 2),
                ),
              ),
              if (!isLast)
                Expanded(
                  child: Container(
                    width: 2,
                    color: Colors.blueAccent.withValues(alpha: 0.3),
                  ),
                ),
            ],
          ),
          const SizedBox(width: 12),
          // Content
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Card(
                elevation: 0,
                margin: EdgeInsets.zero,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(
                    color: ev.isPatientZeroCandidate
                        ? Colors.redAccent.withValues(alpha: 0.4)
                        : Theme.of(context).dividerColor.withValues(alpha: 0.2),
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            ev.source,
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                          ),
                          if (ev.isPatientZeroCandidate)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: Colors.redAccent.withValues(alpha: 0.2),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: const Text(
                                'ORIGIN CANDIDATE',
                                style: TextStyle(
                                  fontSize: 9,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.redAccent,
                                ),
                              ),
                            ),
                          Text(
                            ev.timestamp != null
                                ? DateFormat('MMM dd, yyyy HH:mm').format(ev.timestamp!)
                                : 'Undated',
                            style: const TextStyle(fontSize: 11, color: Colors.grey),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        ev.title ?? ev.snippet ?? 'Mention discovered',
                        style: const TextStyle(fontSize: 13),
                      ),
                      if (ev.url != null && ev.url!.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 10,
                          children: [
                            InkWell(
                              onTap: () => _launchUrl(ev.url),
                              child: const Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(Icons.open_in_new, size: 14, color: Colors.blueAccent),
                                  SizedBox(width: 4),
                                  Text(
                                    'Source Link',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: Colors.blueAccent,
                                      decoration: TextDecoration.underline,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            if (ev.earliestCdxTimestamp != null)
                              Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.history_edu, size: 14, color: Colors.grey),
                                  const SizedBox(width: 4),
                                  Text(
                                    'Wayback Snapshot: ${DateFormat('yyyy-MM-dd').format(ev.earliestCdxTimestamp!)}',
                                    style: const TextStyle(fontSize: 11, color: Colors.grey),
                                  ),
                                ],
                              ),
                          ],
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetaColumn(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 11, color: Colors.grey, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
          overflow: TextOverflow.ellipsis,
        ),
      ],
    );
  }

  Widget _buildProfileRow(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 11, color: Colors.grey, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: const TextStyle(fontSize: 13),
        ),
      ],
    );
  }

  Color _getVerdictColor(String verdict) {
    final v = verdict.toLowerCase();
    if (v.contains('true') || v.contains('confirmed')) {
      return Colors.green;
    } else if (v.contains('misleading') || v.contains('context')) {
      return Colors.orange;
    } else if (v.contains('false') || v.contains('fabricated')) {
      return Colors.red;
    } else if (v.contains('satire')) {
      return Colors.purple;
    }
    return Colors.blueGrey;
  }
}
