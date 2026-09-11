import 'package:flutter_test/flutter_test.dart';
import 'package:truthtrace/main.dart';

void main() {
  testWidgets('TruthTraceApp loads and displays header', (WidgetTester tester) async {
    await tester.pumpWidget(const TruthTraceApp());
    expect(find.text('TruthTrace'), findsOneWidget);
    expect(find.text('Investigate a Claim'), findsOneWidget);
  });
}
