import 'package:flutter/material.dart';
import '../models/package.dart';

class CartProvider with ChangeNotifier {
  final List<StudyAbroadPackage> _items = [];

  List<StudyAbroadPackage> get items => List.unmodifiable(_items);

  void addItem(StudyAbroadPackage package) {
    if (!_items.any((item) => item.id == package.id)) {
      _items.add(package);
      notifyListeners();
    }
  }

  void removeItem(String packageId) {
    _items.removeWhere((item) => item.id == packageId);
    notifyListeners();
  }

  void clear() {
    _items.clear();
    notifyListeners();
  }

  int get count => _items.length;
}
