// // main.dart
// import 'package:flutter/material.dart';
// import 'package:shared_preferences/shared_preferences.dart';
// import 'api_service.dart';

// void main() {
//   runApp(const SkoobSyncApp());
// }

// class SkoobSyncApp extends StatelessWidget {
//   const SkoobSyncApp({super.key});

//   @override
//   Widget build(BuildContext context) {
//     return MaterialApp(
//       title: 'Skoob Sync',
//       theme: ThemeData(
//         primarySwatch: Colors.blue,
//         visualDensity: VisualDensity.adaptivePlatformDensity,
//         fontFamily: 'Inter',
//         inputDecorationTheme: InputDecorationTheme(
//           border: OutlineInputBorder(
//             borderRadius: BorderRadius.circular(12.0),
//           ),
//         ),
//       ),
//       debugShowCheckedModeBanner: false,
//       home: const AuthWrapper(),
//     );
//   }
// }

// class AuthWrapper extends StatefulWidget {
//   const AuthWrapper({super.key});

//   @override
//   State<AuthWrapper> createState() => _AuthWrapperState();
// }

// class _AuthWrapperState extends State<AuthWrapper> {
//   bool _isLoading = true;
//   bool _hasCredentials = false;

//   @override
//   void initState() {
//     super.initState();
//     _checkCredentials();
//   }

//   Future<void> _checkCredentials() async {
//     final prefs = await SharedPreferences.getInstance();
//     final token = prefs.getString('readwise_token');
//     if (token != null && token.isNotEmpty) {
//       setState(() {
//         _hasCredentials = true;
//       });
//     }
//     setState(() {
//       _isLoading = false;
//     });
//   }

//   void _onLoginSuccess() {
//     setState(() {
//       _hasCredentials = true;
//     });
//   }

//   void _onLogout() {
//     setState(() {
//       _hasCredentials = false;
//     });
//   }

//   @override
//   Widget build(BuildContext context) {
//     if (_isLoading) {
//       return const Scaffold(body: Center(child: CircularProgressIndicator()));
//     }
//     if (_hasCredentials) {
//       return SyncScreen(onLogout: _onLogout);
//     } else {
//       return LoginScreen(onLoginSuccess: _onLoginSuccess);
//     }
//   }
// }

// class LoginScreen extends StatefulWidget {
//   final VoidCallback onLoginSuccess;
//   const LoginScreen({super.key, required this.onLoginSuccess});

//   @override
//   State<LoginScreen> createState() => _LoginScreenState();
// }

// class _LoginScreenState extends State<LoginScreen> {
//   final _skoobUserController = TextEditingController();
//   final _skoobPassController = TextEditingController();
//   final _readwiseTokenController = TextEditingController();
//   bool _isSaving = false;

//   // Esta função apenas salva os dados localmente, sem verificar.
//   Future<void> _saveCredentials() async {
//     if (_skoobUserController.text.isEmpty ||
//         _skoobPassController.text.isEmpty ||
//         _readwiseTokenController.text.isEmpty) {
//       ScaffoldMessenger.of(context).showSnackBar(
//         const SnackBar(content: Text('Por favor, preencha todos os campos.')),
//       );
//       return;
//     }

//     setState(() => _isSaving = true);

//     final prefs = await SharedPreferences.getInstance();
//     await prefs.setString('skoob_user', _skoobUserController.text);
//     await prefs.setString('skoob_pass', _skoobPassController.text);
//     await prefs.setString('readwise_token', _readwiseTokenController.text);

//     setState(() => _isSaving = false);

//     widget.onLoginSuccess();
//   }

//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       body: Center(
//         child: SingleChildScrollView(
//           padding: const EdgeInsets.all(32.0),
//           child: Column(
//             mainAxisAlignment: MainAxisAlignment.center,
//             crossAxisAlignment: CrossAxisAlignment.stretch,
//             children: [
//               const Text(
//                 'Bem-vinda',
//                 textAlign: TextAlign.center,
//                 style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
//               ),
//               const SizedBox(height: 8),
//               const Text(
//                 'Insira as suas credenciais para começar.',
//                 textAlign: TextAlign.center,
//                 style: TextStyle(fontSize: 16, color: Colors.grey),
//               ),
//               const SizedBox(height: 48),
//               TextField(
//                 controller: _skoobUserController,
//                 decoration: const InputDecoration(labelText: 'Email do Skoob'),
//                 keyboardType: TextInputType.emailAddress,
//               ),
//               const SizedBox(height: 16),
//               TextField(
//                 controller: _skoobPassController,
//                 decoration: const InputDecoration(labelText: 'Senha do Skoob'),
//                 obscureText: true,
//               ),
//               const SizedBox(height: 16),
//               TextField(
//                 controller: _readwiseTokenController,
//                 decoration: const InputDecoration(labelText: 'Token do Readwise'),
//               ),
//               const SizedBox(height: 32),
//               ElevatedButton(
//                 onPressed: _isSaving ? null : _saveCredentials,
//                 style: ElevatedButton.styleFrom(
//                   padding: const EdgeInsets.symmetric(vertical: 16),
//                   shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
//                 ),
//                 child: _isSaving
//                     ? const CircularProgressIndicator(color: Colors.white)
//                     : const Text('Salvar e Continuar', style: TextStyle(fontSize: 16)),
//               ),
//             ],
//           ),
//         ),
//       ),
//     );
//   }
// }

// class SyncScreen extends StatefulWidget {
//   final VoidCallback onLogout;
//   const SyncScreen({super.key, required this.onLogout});

//   @override
//   State<SyncScreen> createState() => _SyncScreenState();
// }

// class _SyncScreenState extends State<SyncScreen> {
//   final _bookTitleController = TextEditingController();
//   int _selectedStatusId = 2;
//   bool _isLoading = false;
//   String _message = '';
//   bool _isError = false;

//   final ApiService _apiService = ApiService();

//   Future<void> _handleSync() async {
//     if (_bookTitleController.text.isEmpty) {
//       setState(() {
//         _message = 'Por favor, insira o título do livro.';
//         _isError = true;
//       });
//       return;
//     }

//     setState(() {
//       _isLoading = true;
//       _message = '';
//     });

//     try {
//       final prefs = await SharedPreferences.getInstance();
//       final skoobUser = prefs.getString('skoob_user');
//       final skoobPass = prefs.getString('skoob_pass');
//       final readwiseToken = prefs.getString('readwise_token');

//       final successMessage = await _apiService.syncSkoobProgress(
//         skoobUser: skoobUser,
//         skoobPass: skoobPass,
//         readwiseToken: readwiseToken,
//         bookTitle: _bookTitleController.text,
//         statusId: _selectedStatusId,
//       );
      
//       setState(() {
//         _message = successMessage;
//         _isError = false;
//       });

//     } catch (e) {
//       setState(() {
//         _message = e.toString();
//         _isError = true;
//       });
//     } finally {
//       setState(() {
//         _isLoading = false;
//       });
//     }
//   }
  
//   Future<void> _handleLogout() async {
//     final prefs = await SharedPreferences.getInstance();
//     await prefs.clear();
//     widget.onLogout();
//   }

//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       appBar: AppBar(
//         title: const Text('Skoob Sync'),
//         actions: [
//           IconButton(
//             icon: const Icon(Icons.logout),
//             tooltip: 'Sair',
//             onPressed: _handleLogout,
//           )
//         ],
//       ),
//       body: SingleChildScrollView(
//         padding: const EdgeInsets.all(24.0),
//         child: Column(
//           crossAxisAlignment: CrossAxisAlignment.stretch,
//           children: [
//             const Text(
//               'Sincronizar Progresso',
//               style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
//             ),
//             const SizedBox(height: 24),
//             TextField(
//               controller: _bookTitleController,
//               decoration: const InputDecoration(
//                 labelText: 'Título do Livro',
//                 hintText: 'Exatamente como no Kindle',
//               ),
//             ),
//             const SizedBox(height: 16),
//             DropdownButtonFormField<int>(
//               value: _selectedStatusId,
//               decoration: const InputDecoration(
//                 labelText: 'Atualizar estado para',
//               ),
//               items: const [
//                 DropdownMenuItem(value: 2, child: Text('Lendo (publicar progresso)')),
//                 DropdownMenuItem(value: 4, child: Text('Relendo (publicar progresso)')),
//                 DropdownMenuItem(value: 1, child: Text('Lido')),
//                 DropdownMenuItem(value: 3, child: Text('Quero ler')),
//                 DropdownMenuItem(value: 5, child: Text('Abandonei')),
//               ],
//               onChanged: (value) {
//                 if (value != null) {
//                   setState(() {
//                     _selectedStatusId = value;
//                   });
//                 }
//               },
//             ),
//             const SizedBox(height: 32),
//             ElevatedButton.icon(
//               onPressed: _isLoading ? null : _handleSync,
//               icon: _isLoading ? Container() : const Icon(Icons.sync),
//               label: Text(_isLoading ? 'Sincronizando...' : 'Sincronizar Agora'),
//               style: ElevatedButton.styleFrom(
//                 padding: const EdgeInsets.symmetric(vertical: 16),
//                 textStyle: const TextStyle(fontSize: 16),
//               ),
//             ),
//             if (_isLoading)
//               const Padding(
//                 padding: EdgeInsets.only(top: 16.0),
//                 child: Center(child: CircularProgressIndicator()),
//               ),
//             if (_message.isNotEmpty)
//               Padding(
//                 padding: const EdgeInsets.only(top: 16.0),
//                 child: Text(
//                   _message,
//                   textAlign: TextAlign.center,
//                   style: TextStyle(
//                     color: _isError ? Colors.red : Colors.green,
//                     fontWeight: FontWeight.bold,
//                   ),
//                 ),
//               ),
//           ],
//         ),
//       ),
//     );
//   }
// }

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
        primarySwatch: Colors.indigo,
        useMaterial3: true,
        visualDensity: VisualDensity.adaptivePlatformDensity,
        fontFamily: 'Inter',
        inputDecorationTheme: InputDecorationTheme(
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12.0),
          ),
          filled: true,
          fillColor: Colors.grey[50],
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            padding: const EdgeInsets.symmetric(vertical: 16),
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
  String? _connectionError;

  @override
  void initState() {
    super.initState();
    _checkCredentialsAndConnection();
  }

  Future<void> _checkCredentialsAndConnection() async {
    // Verifica credenciais salvas
    final prefs = await SharedPreferences.getInstance();
    final skoobUser = prefs.getString('skoob_user');
    final skoobPass = prefs.getString('skoob_pass');
    final readwiseToken = prefs.getString('readwise_token');
    
    bool hasAllCredentials = skoobUser != null && 
                           skoobUser.isNotEmpty &&
                           skoobPass != null && 
                           skoobPass.isNotEmpty &&
                           readwiseToken != null && 
                           readwiseToken.isNotEmpty;

    // Testa conexão com a API se tem credenciais
    if (hasAllCredentials) {
      final apiService = ApiService();
      final connectionTest = await apiService.testConnection();
      
      if (!connectionTest['success']) {
        setState(() {
          _connectionError = connectionTest['error'];
        });
      }
    }

    setState(() {
      _hasCredentials = hasAllCredentials;
      _isLoading = false;
    });
  }

  void _onLoginSuccess() {
    setState(() {
      _hasCredentials = true;
      _connectionError = null;
    });
  }

  void _onLogout() {
    setState(() {
      _hasCredentials = false;
      _connectionError = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Carregando...'),
            ],
          ),
        ),
      );
    }

    // Mostra erro de conexão se houver
    if (_connectionError != null) {
      return Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.wifi_off,
                  size: 64,
                  color: Colors.red,
                ),
                const SizedBox(height: 24),
                const Text(
                  'Problema de Conexão',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),
                Text(
                  _connectionError!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 16, color: Colors.grey),
                ),
                const SizedBox(height: 32),
                ElevatedButton(
                  onPressed: () {
                    setState(() {
                      _isLoading = true;
                      _connectionError = null;
                    });
                    _checkCredentialsAndConnection();
                  },
                  child: const Text('Tentar Novamente'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    if (_hasCredentials) {
      return SyncScreen(onLogout: _onLogout);
    } else {
      return LoginScreen(onLoginSuccess: _onLoginSuccess);
    }
  }
}

class LoginScreen extends StatefulWidget {
  final VoidCallback onLoginSuccess;
  const LoginScreen({super.key, required this.onLoginSuccess});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _skoobUserController = TextEditingController();
  final _skoobPassController = TextEditingController();
  final _readwiseTokenController = TextEditingController();
  bool _isSaving = false;
  bool _obscurePassword = true;

  @override
  void dispose() {
    _skoobUserController.dispose();
    _skoobPassController.dispose();
    _readwiseTokenController.dispose();
    super.dispose();
  }

  String? _validateEmail(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Email é obrigatório';
    }
    if (!value.contains('@')) {
      return 'Email inválido';
    }
    return null;
  }

  String? _validatePassword(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Senha é obrigatória';
    }
    if (value.length < 3) {
      return 'Senha muito curta';
    }
    return null;
  }

  String? _validateToken(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Token é obrigatório';
    }
    if (value.length < 10) {
      return 'Token parece inválido';
    }
    return null;
  }

  Future<void> _saveCredentials() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _isSaving = true);

    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('skoob_user', _skoobUserController.text.trim());
      await prefs.setString('skoob_pass', _skoobPassController.text.trim());
      await prefs.setString('readwise_token', _readwiseTokenController.text.trim());

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Credenciais salvas com sucesso!'),
            backgroundColor: Colors.green,
          ),
        );
        widget.onLoginSuccess();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erro ao salvar: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(32.0),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Logo/Título
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: Theme.of(context).primaryColor.withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.sync,
                      size: 48,
                      color: Theme.of(context).primaryColor,
                    ),
                  ),
                  const SizedBox(height: 32),
                  const Text(
                    'Bem-vindo!',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Configure suas credenciais para sincronizar seus livros',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 16, color: Colors.grey),
                  ),
                  const SizedBox(height: 48),
                  
                  // Campos do formulário
                  TextFormField(
                    controller: _skoobUserController,
                    decoration: const InputDecoration(
                      labelText: 'Email do Skoob',
                      prefixIcon: Icon(Icons.email),
                      hintText: 'seu@email.com',
                    ),
                    keyboardType: TextInputType.emailAddress,
                    textInputAction: TextInputAction.next,
                    validator: _validateEmail,
                  ),
                  const SizedBox(height: 16),
                  
                  TextFormField(
                    controller: _skoobPassController,
                    decoration: InputDecoration(
                      labelText: 'Senha do Skoob',
                      prefixIcon: const Icon(Icons.lock),
                      suffixIcon: IconButton(
                        icon: Icon(_obscurePassword ? Icons.visibility : Icons.visibility_off),
                        onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                      ),
                    ),
                    obscureText: _obscurePassword,
                    textInputAction: TextInputAction.next,
                    validator: _validatePassword,
                  ),
                  const SizedBox(height: 16),
                  
                  TextFormField(
                    controller: _readwiseTokenController,
                    decoration: const InputDecoration(
                      labelText: 'Token do Readwise',
                      prefixIcon: Icon(Icons.key),
                      hintText: 'Cole aqui seu token',
                    ),
                    textInputAction: TextInputAction.done,
                    validator: _validateToken,
                    onFieldSubmitted: (_) => _saveCredentials(),
                  ),
                  const SizedBox(height: 8),
                  
                  // Link para ajuda
                  TextButton(
                    onPressed: () {
                      showDialog(
                        context: context,
                        builder: (context) => AlertDialog(
                          title: const Text('Como obter o Token do Readwise'),
                          content: const Text(
                            '1. Acesse readwise.io\n'
                            '2. Faça login na sua conta\n'
                            '3. Vá em Settings → API\n'
                            '4. Copie o Access Token\n'
                            '5. Cole aqui no campo acima',
                          ),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.pop(context),
                              child: const Text('Entendi'),
                            ),
                          ],
                        ),
                      );
                    },
                    child: const Text('Como obter o token do Readwise?'),
                  ),
                  const SizedBox(height: 32),
                  
                  // Botão de salvar
                  ElevatedButton(
                    onPressed: _isSaving ? null : _saveCredentials,
                    child: _isSaving
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Salvar e Continuar', style: TextStyle(fontSize: 16)),
                  ),
                ],
              ),
            ),
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
  final _formKey = GlobalKey<FormState>();
  final _bookTitleController = TextEditingController();
  int _selectedStatusId = 2;
  bool _isLoading = false;
  SyncResult? _lastResult;

  final ApiService _apiService = ApiService();

  final Map<int, String> _statusOptions = {
    2: 'Lendo (com progresso)',
    4: 'Relendo (com progresso)',
    1: 'Lido',
    3: 'Quero ler',
    5: 'Abandonei',
  };

  final Map<int, IconData> _statusIcons = {
    1: Icons.check_circle,
    2: Icons.auto_stories,
    3: Icons.bookmark_add,
    4: Icons.refresh,
    5: Icons.close,
  };

  @override
  void dispose() {
    _bookTitleController.dispose();
    super.dispose();
  }

  Future<void> _handleSync() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
      _lastResult = null;
    });

    try {
      final prefs = await SharedPreferences.getInstance();
      final skoobUser = prefs.getString('skoob_user');
      final skoobPass = prefs.getString('skoob_pass');
      final readwiseToken = prefs.getString('readwise_token');

      final result = await _apiService.syncSkoobProgress(
        skoobUser: skoobUser,
        skoobPass: skoobPass,
        readwiseToken: readwiseToken,
        bookTitle: _bookTitleController.text,
        statusId: _selectedStatusId,
      );

      setState(() {
        _lastResult = result;
      });

      if (mounted && result.isSuccess) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result.message),
            backgroundColor: Colors.green,
            action: SnackBarAction(
              label: 'Ver Detalhes',
              onPressed: () => _showResultDetails(result),
            ),
          ),
        );
      }

    } catch (e) {
      final errorResult = SyncResult.error(error: e.toString());
      setState(() {
        _lastResult = errorResult;
      });

      if (mounted) {
        _showErrorDialog(e);
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _showResultDetails(SyncResult result) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Detalhes da Sincronização'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Status: ${result.isSuccess ? "Sucesso" : "Erro"}'),
            const SizedBox(height: 8),
            Text('Mensagem: ${result.message}'),
            if (result.details != null) ...[
              const SizedBox(height: 8),
              const Text('Detalhes:', style: TextStyle(fontWeight: FontWeight.bold)),
              ...result.details!.entries.map((e) => 
                Text('${e.key}: ${e.value}')
              ),
            ],
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Fechar'),
          ),
        ],
      ),
    );
  }

  void _showErrorDialog(dynamic error) {
    String title = 'Erro na Sincronização';
    String message = error.toString();
    IconData icon = Icons.error;
    Color iconColor = Colors.red;

    if (error is AuthenticationException) {
      title = 'Erro de Login';
      icon = Icons.lock;
      iconColor = Colors.orange;
    } else if (error is ValidationException) {
      title = 'Dados Inválidos';
      icon = Icons.warning;
      iconColor = Colors.amber;
    } else if (error is ConnectionException) {
      title = 'Erro de Conexão';
      icon = Icons.wifi_off;
      iconColor = Colors.blue;
    } else if (error is TimeoutException) {
      title = 'Timeout';
      icon = Icons.timer;
      iconColor = Colors.purple;
    }

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(icon, color: iconColor),
            const SizedBox(width: 8),
            Text(title),
          ],
        ),
        content: SingleChildScrollView(
          child: Text(message),
        ),
        actions: [
          if (error is AuthenticationException)
            TextButton(
              onPressed: () {
                Navigator.pop(context);
                _handleLogout();
              },
              child: const Text('Reconfigurar'),
            ),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Fechar'),
          ),
        ],
      ),
    );
  }

  Future<void> _handleLogout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirmar Logout'),
        content: const Text('Isso irá remover todas as credenciais salvas. Deseja continuar?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Sair'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.clear();
      widget.onLogout();
    }
  }

  String? _validateBookTitle(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Título do livro é obrigatório';
    }
    if (value.trim().length < 2) {
      return 'Título muito curto';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Skoob Sync'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            tooltip: 'Sobre',
            onPressed: () => _showAboutDialog(),
          ),
          PopupMenuButton(
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'test_connection',
                child: ListTile(
                  leading: Icon(Icons.network_check),
                  title: Text('Testar Conexão'),
                ),
              ),
              const PopupMenuItem(
                value: 'logout',
                child: ListTile(
                  leading: Icon(Icons.logout, color: Colors.red),
                  title: Text('Sair', style: TextStyle(color: Colors.red)),
                ),
              ),
            ],
            onSelected: (value) {
              switch (value) {
                case 'test_connection':
                  _testConnection();
                  break;
                case 'logout':
                  _handleLogout();
                  break;
              }
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      Theme.of(context).primaryColor.withOpacity(0.1),
                      Theme.of(context).primaryColor.withOpacity(0.05),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Column(
                  children: [
                    Icon(Icons.sync, size: 48, color: Colors.indigo),
                    SizedBox(height: 8),
                    Text(
                      'Sincronizar Progresso',
                      style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Atualize seu progresso do Kindle no Skoob',
                      style: TextStyle(color: Colors.grey),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),

              // Campo do título do livro
              TextFormField(
                controller: _bookTitleController,
                decoration: const InputDecoration(
                  labelText: 'Título do Livro',
                  hintText: 'Digite exatamente como aparece no Kindle',
                  prefixIcon: Icon(Icons.book),
                  helperText: 'Use o título exato que aparece no seu Kindle',
                ),
                textInputAction: TextInputAction.done,
                validator: _validateBookTitle,
                onFieldSubmitted: (_) => _handleSync(),
              ),
              const SizedBox(height: 24),

              // Seletor de status
              DropdownButtonFormField<int>(
                value: _selectedStatusId,
                decoration: const InputDecoration(
                  labelText: 'Status no Skoob',
                  prefixIcon: Icon(Icons.category),
                ),
                items: _statusOptions.entries.map((entry) {
                  return DropdownMenuItem(
                    value: entry.key,
                    child: Row(
                      children: [
                        Icon(_statusIcons[entry.key], size: 20),
                        const SizedBox(width: 8),
                        Text(entry.value),
                      ],
                    ),
                  );
                }).toList(),
                onChanged: (value) {
                  if (value != null) {
                    setState(() {
                      _selectedStatusId = value;
                    });
                  }
                },
              ),
              const SizedBox(height: 32),

              // Botão de sincronização
              ElevatedButton.icon(
                onPressed: _isLoading ? null : _handleSync,
                icon: _isLoading 
                  ? const SizedBox(
                      width: 20, 
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.sync),
                label: Text(
                  _isLoading ? 'Sincronizando...' : 'Sincronizar Agora',
                  style: const TextStyle(fontSize: 16),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Theme.of(context).primaryColor,
                  foregroundColor: Colors.white,
                  minimumSize: const Size.fromHeight(56),
                ),
              ),

              // Resultado da última sincronização
              if (_lastResult != null) ...[
                const SizedBox(height: 24),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: _lastResult!.isSuccess 
                      ? Colors.green.withOpacity(0.1)
                      : Colors.red.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: _lastResult!.isSuccess 
                        ? Colors.green.withOpacity(0.3)
                        : Colors.red.withOpacity(0.3),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            _lastResult!.isSuccess 
                              ? Icons.check_circle 
                              : Icons.error,
                            color: _lastResult!.isSuccess 
                              ? Colors.green 
                              : Colors.red,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _lastResult!.isSuccess 
                                ? 'Sucesso!' 
                                : 'Erro',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                color: _lastResult!.isSuccess 
                                  ? Colors.green[700] 
                                  : Colors.red[700],
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(_lastResult!.message),
                      if (_lastResult!.details != null && _lastResult!.isSuccess) ...[
                        const SizedBox(height: 8),
                        const Divider(),
                        ...(_lastResult!.details!.entries.map((entry) =>
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 2),
                            child: Row(
                              children: [
                                Text(
                                  '${entry.key}: ',
                                  style: const TextStyle(fontWeight: FontWeight.w500),
                                ),
                                Expanded(child: Text('${entry.value}')),
                              ],
                            ),
                          )
                        ).toList()),
                      ],
                    ],
                  ),
                ),
              ],
              
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  void _showAboutDialog() {
    showAboutDialog(
      context: context,
      applicationName: 'Skoob Sync',
      applicationVersion: '2.0',
      applicationIcon: const Icon(Icons.sync, size: 48),
      children: const [
        Text(
          'Sincroniza automaticamente seu progresso de leitura do Kindle (via Readwise) com o Skoob.\n\n'
          'Desenvolvido para facilitar o acompanhamento das suas leituras.',
        ),
      ],
    );
  }

  Future<void> _testConnection() async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const AlertDialog(
        content: Row(
          children: [
            CircularProgressIndicator(),
            SizedBox(width: 16),
            Text('Testando conexão...'),
          ],
        ),
      ),
    );

    try {
      final result = await _apiService.testConnection();
      
      Navigator.pop(context); // Fecha o dialog de loading
      
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Row(
            children: [
              Icon(
                result['success'] ? Icons.check_circle : Icons.error,
                color: result['success'] ? Colors.green : Colors.red,
              ),
              const SizedBox(width: 8),
              Text(result['success'] ? 'Conectado!' : 'Erro de Conexão'),
            ],
          ),
          content: Text(
            result['success'] 
              ? 'Conexão com a API estabelecida com sucesso!'
              : 'Falha na conexão: ${result['error']}',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Fechar'),
            ),
          ],
        ),
      );
    } catch (e) {
      Navigator.pop(context); // Fecha o dialog de loading
      
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.error, color: Colors.red),
              SizedBox(width: 8),
              Text('Erro'),
            ],
          ),
          content: Text('Erro no teste: $e'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Fechar'),
            ),
          ],
        ),
      );
    }
  }
}