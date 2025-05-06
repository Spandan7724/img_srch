// lib/main.dart

import 'package:flutter/material.dart';
import 'package:window_manager/window_manager.dart';
import 'package:hotkey_manager/hotkey_manager.dart';
import 'package:flutter/services.dart';
import 'screens/home_screen.dart';

const Size _initialSize = Size(600, 80);
const double _verticalOffset = 200;

Future<void> main() async {
  // 1. Initialize Flutter bindings
  WidgetsFlutterBinding.ensureInitialized();

  // 2. Initialize window manager
  await windowManager.ensureInitialized();

  // 3. Register global Alt+S hotkey
  await hotKeyManager.unregisterAll();
  final hotKey = HotKey(
    key: PhysicalKeyboardKey.keyS,
    modifiers: [HotKeyModifier.alt],
    scope: HotKeyScope.system,
  );
  await hotKeyManager.register(
    hotKey,
    keyDownHandler: (hotKey) async {
      final isVisible = await windowManager.isVisible();
      if (isVisible) {
        await windowManager.hide();
      } else {
        // Reset to original size on every show
        await windowManager.setSize(_initialSize);
        // Show, focus, and reposition
        await windowManager.show();
        await windowManager.focus();
        await windowManager.center();
        final bounds = await windowManager.getBounds();
        await windowManager.setPosition(Offset(bounds.left, _verticalOffset));
      }
    },
  );

  // 4. Configure window options
  WindowOptions options = WindowOptions(
    size: _initialSize,
    minimumSize: _initialSize,
    titleBarStyle: TitleBarStyle.hidden,
    backgroundColor: Colors.transparent,
    skipTaskbar: true,
    alwaysOnTop: true,
  );

  // 5. Wait until ready, then show & reset size
  windowManager.waitUntilReadyToShow(options, () async {
    await windowManager.setSize(_initialSize);
    await windowManager.show();
    await windowManager.focus();
    await windowManager.center();
    final bounds = await windowManager.getBounds();
    await windowManager.setPosition(Offset(bounds.left, _verticalOffset));
  });

  // 6. Launch the Flutter app
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Image Search Launcher',
      debugShowCheckedModeBanner: false,
      home: const HomeScreen(),
    );
  }
}
