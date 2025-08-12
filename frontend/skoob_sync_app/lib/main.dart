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
    if (token != null && token.trim().isNotEmpty) {
      _hasCredentials = true;
    }
    setState(() => _isLoading = false);
  }

  void _onLoginSuccess() {
    setState(() => _hasCredentials = true);
  }

  void _onLogout() {
    setState(() => _hasCredentials = false);
  }

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
    if (_skoobUserController.text.trim().isEmpty ||
        _skoobPassController.text.trim().isEmpty ||
        _readwiseTokenController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Por favor, preencha todos os campos.')),
      );
      return;
    }

    setState(() => _isSaving = true);

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('skoob_user', _skoobUserController.text.trim());
    await prefs.setString('skoob_pass', _skoobPassController.text.trim());
    await prefs.setString('readwise_token', _readwiseTokenController.text.trim());

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
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Bem-vinda',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Text(
                'Insira as suas credenciais para começar.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16, color: Colors.grey),
              ),
              const SizedBox(height: 48),
              TextField(
                controller: _skoobUserController,
                decoration: const InputDecoration(labelText: 'Email do Skoob'),
                keyboardType: TextInputType.emailAddress,
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
                decoration: const InputDecoration(labelText: 'Token do Readwise'),
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: _isSaving ? null : _saveCredentials,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: _isSaving
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text('Salvar e Continuar', style: TextStyle(fontSize: 16)),
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
    if (_bookTitleController.text.trim().isEmpty) {
      setState(() {
        _message = 'Por favor, insira o título do livro.';
        _isError = true;
      });
      return;
    }

    final prefs = await SharedPreferences.getInstance();
    final skoobUser = prefs.getString('skoob_user') ?? '';
    final skoobPass = prefs.getString('skoob_pass') ?? '';
    final readwiseToken = prefs.getString('readwise_token') ?? '';

    if ([skoobUser, skoobPass, readwiseToken].any((v) => v.trim().isEmpty)) {
      setState(() {
        _message = 'Credenciais incompletas. Faça login novamente.';
        _isError = true;
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _message = '';
    });

    try {
      print('📦 Enviando para API: {'
          'skoob_user: $skoobUser, '
          'skoob_pass: $skoobPass, '
          'readwise_token: $readwiseToken, '
          'book_title: ${_bookTitleController.text.trim()}, '
          'status_id: $_selectedStatusId'
          '}');

      final successMessage = await _apiService.syncSkoobProgress(
        skoobUser: skoobUser,
        skoobPass: skoobPass,
        readwiseToken: readwiseToken,
        bookTitle: _bookTitleController.text.trim(),
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
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Sair',
            onPressed: _handleLogout,
          )
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Sincronizar Progresso',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 24),
            TextField(
              controller: _bookTitleController,
              decoration: const InputDecoration(
                labelText: 'Título do Livro',
                hintText: 'Exatamente como no Kindle',
              ),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<int>(
              value: _selectedStatusId,
              decoration: const InputDecoration(
                labelText: 'Atualizar estado para',
              ),
              items: const [
                DropdownMenuItem(value: 2, child: Text('Lendo (publicar progresso)')),
                DropdownMenuItem(value: 4, child: Text('Relendo (publicar progresso)')),
                DropdownMenuItem(value: 1, child: Text('Lido')),
                DropdownMenuItem(value: 3, child: Text('Quero ler')),
                DropdownMenuItem(value: 5, child: Text('Abandonei')),
              ],
              onChanged: (value) {
                if (value != null) {
                  setState(() => _selectedStatusId = value);
                }
              },
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _handleSync,
              icon: _isLoading ? Container() : const Icon(Icons.sync),
              label: Text(_isLoading ? 'Sincronizando...' : 'Sincronizar Agora'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                textStyle: const TextStyle(fontSize: 16),
              ),
            ),
            if (_isLoading)
              const Padding(
                padding: EdgeInsets.only(top: 16.0),
                child: Center(child: CircularProgressIndicator()),
              ),
            if (_message.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 16.0),
                child: Text(
                  _message,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: _isError ? Colors.red : Colors.green,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
