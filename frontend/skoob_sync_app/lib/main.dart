import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

void main() {
  runApp(const SkoobSyncApp());
}

class SkoobSyncApp extends StatelessWidget {
  const SkoobSyncApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Skoob Sync',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
        fontFamily: 'Inter',
        inputDecorationTheme: InputDecorationTheme(
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12.0),
          ),
        ),
      ),
      debugShowCheckedModeBanner: false,
      home: const AuthWrapper(),
    );
  }
}

class AuthWrapper extends StatefulWidget {
  const AuthWrapper({super.key});

  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  bool _isLoading = true;
  bool _hasCredentials = false;

  @override
  void initState() {
    super.initState();
    _checkCredentials();
  }

  Future<void> _checkCredentials() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('readwise_token');
    final user = prefs.getString('skoob_user');
    final pass = prefs.getString('skoob_pass');

    if (token != null && user != null && pass != null && 
        token.isNotEmpty && user.isNotEmpty && pass.isNotEmpty) {
      setState(() => _hasCredentials = true);
    }

    setState(() => _isLoading = false);
  }

  void _onLoginSuccess() => setState(() => _hasCredentials = true);

  void _onLogout() => setState(() => _hasCredentials = false);

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return _hasCredentials
        ? SyncScreen(onLogout: _onLogout)
        : LoginScreen(onLoginSuccess: _onLoginSuccess);
  }
}

class LoginScreen extends StatefulWidget {
  final VoidCallback onLoginSuccess;
  const LoginScreen({super.key, required this.onLoginSuccess});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _skoobUserController = TextEditingController();
  final _skoobPassController = TextEditingController();
  final _readwiseTokenController = TextEditingController();
  bool _isSaving = false;

  Future<void> _saveCredentials() async {
    if (_skoobUserController.text.isEmpty ||
        _skoobPassController.text.isEmpty ||
        _readwiseTokenController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Preencha todos os campos.')),
      );
      return;
    }

    setState(() => _isSaving = true);

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('skoob_user', _skoobUserController.text);
    await prefs.setString('skoob_pass', _skoobPassController.text);
    await prefs.setString('readwise_token', _readwiseTokenController.text);

    setState(() => _isSaving = false);
    widget.onLoginSuccess();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            children: [
              const Text('Bem-vinda',
                  style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              const Text('Insira as suas credenciais para começar.',
                  style: TextStyle(fontSize: 16, color: Colors.grey)),
              const SizedBox(height: 48),
              TextField(
                controller: _skoobUserController,
                decoration: const InputDecoration(labelText: 'Email do Skoob'),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _skoobPassController,
                decoration: const InputDecoration(labelText: 'Senha do Skoob'),
                obscureText: true,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _readwiseTokenController,
                decoration:
                    const InputDecoration(labelText: 'Token do Readwise'),
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: _isSaving ? null : _saveCredentials,
                child: _isSaving
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text('Salvar e Continuar'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class SyncScreen extends StatefulWidget {
  final VoidCallback onLogout;
  const SyncScreen({super.key, required this.onLogout});

  @override
  State<SyncScreen> createState() => _SyncScreenState();
}

class _SyncScreenState extends State<SyncScreen> {
  final _bookTitleController = TextEditingController();
  int _selectedStatusId = 2;
  bool _isLoading = false;
  String _message = '';
  bool _isError = false;

  final ApiService _apiService = ApiService();

  Future<void> _handleSync() async {
    setState(() {
      _message = '';
      _isError = false;
    });

    final prefs = await SharedPreferences.getInstance();
    final skoobUser = prefs.getString('skoob_user') ?? '';
    final skoobPass = prefs.getString('skoob_pass') ?? '';
    final readwiseToken = prefs.getString('readwise_token') ?? '';
    final bookTitle = _bookTitleController.text.trim();

    // Validação antes da chamada
    if ([skoobUser, skoobPass, readwiseToken, bookTitle].any((v) => v.isEmpty)) {
      setState(() {
        _message = 'Todos os campos e credenciais são obrigatórios.';
        _isError = true;
      });
      return;
    }

    setState(() => _isLoading = true);

    try {
      final successMessage = await _apiService.syncSkoobProgress(
        skoobUser: skoobUser,
        skoobPass: skoobPass,
        readwiseToken: readwiseToken,
        bookTitle: bookTitle,
        statusId: _selectedStatusId,
      );

      setState(() {
        _message = successMessage;
        _isError = false;
      });
    } catch (e) {
      setState(() {
        _message = e.toString();
        _isError = true;
      });
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _handleLogout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
    widget.onLogout();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Skoob Sync'),
        actions: [
          IconButton(icon: const Icon(Icons.logout), onPressed: _handleLogout)
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            TextField(
              controller: _bookTitleController,
              decoration:
                  const InputDecoration(labelText: 'Título do Livro'),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<int>(
              value: _selectedStatusId,
              items: const [
                DropdownMenuItem(value: 2, child: Text('Lendo')),
                DropdownMenuItem(value: 4, child: Text('Relendo')),
                DropdownMenuItem(value: 1, child: Text('Lido')),
                DropdownMenuItem(value: 3, child: Text('Quero ler')),
                DropdownMenuItem(value: 5, child: Text('Abandonei')),
              ],
              onChanged: (value) => setState(() => _selectedStatusId = value!),
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _handleSync,
              icon: _isLoading
                  ? const SizedBox.shrink()
                  : const Icon(Icons.sync),
              label: Text(_isLoading ? 'Sincronizando...' : 'Sincronizar Agora'),
            ),
            if (_message.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 16.0),
                child: Text(
                  _message,
                  style: TextStyle(
                    color: _isError ? Colors.red : Colors.green,
                  ),
                ),
              )
          ],
        ),
      ),
    );
  }
}
