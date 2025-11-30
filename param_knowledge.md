# 模型参数信息

## 1. 参数数据类型定义
定义各模型参数对应的数据类型（完整版本，去重处理）

| 参数名 | 数据类型 | 所属模型 |
|--------|----------|----------|
| **通用参数** | | |
| random_state | int | 通用 |
| n_jobs | int | 通用 |
| **随机森林 (RandomForestRegressor / RandomForestClassifier)** | | |
| n_estimators | int | 随机森林 |
| criterion | select | 随机森林 |
| max_depth | int | 随机森林 |
| min_samples_split | int | 随机森林 |
| min_samples_leaf | int | 随机森林 |
| min_weight_fraction_leaf | float | 随机森林 |
| max_features | select | 随机森林 |
| max_leaf_nodes | int | 随机森林 |
| min_impurity_decrease | float | 随机森林 |
| bootstrap | bool | 随机森林 |
| oob_score | bool | 随机森林 |
| ccp_alpha | float | 随机森林 |
| max_samples | int | 随机森林 |
| **梯度提升树 (GradientBoostingRegressor / GradientBoostingClassifier)** | | |
| learning_rate | float | 梯度提升树 |
| subsample | float | 梯度提升树 |
| validation_fraction | float | 梯度提升树 |
| n_iter_no_change | int | 梯度提升树 |
| tol | float | 梯度提升树 |
| init | select | 梯度提升树（estimator 或 None） |
| warm_start | bool | 梯度提升树 |
| **线性回归 (LinearRegression)** | | |
| fit_intercept | bool | 线性回归 |
| normalize | bool | 线性回归（已弃用） |
| copy_X | bool | 线性回归 |
| positive | bool | 线性回归 |
| **Logistic回归 (LogisticRegression)** | | |
| penalty | select | Logistic回归 |
| dual | bool | Logistic回归 |
| C | float | Logistic回归 |
| intercept_scaling | float | Logistic回归 |
| class_weight | select | Logistic回归 |
| solver | select | Logistic回归 |
| multi_class | select | Logistic回归 |
| l1_ratio | float | Logistic回归（elasticnet） |
| **支持向量机 (SVR / SVC)** | | |
| kernel | select | 支持向量机 |
| degree | int | 支持向量机 |
| gamma | select | 支持向量机 |
| coef0 | float | 支持向量机 |
| shrinking | bool | 支持向量机 |
| cache_size | int | 支持向量机 |
| verbose | bool | 支持向量机 |
| max_iter | int | 支持向量机 |
| epsilon | float | 支持向量机（SVR） |
| probability | bool | 支持向量机（SVC） |
| **决策树 (DecisionTreeRegressor / DecisionTreeClassifier)** | | |
| splitter | select | 决策树 |
| **KNN (KNeighborsRegressor / KNeighborsClassifier)** | | |
| n_neighbors | int | KNN |
| weights | select | KNN |
| algorithm | select | KNN |
| leaf_size | int | KNN |
| p | int | KNN |
| metric | select | KNN |
| metric_params | dict | KNN |

## 2. 枚举类型参数可选值
定义枚举类型参数的可选值（完整版本，去重处理）

| 参数名 | 可选值 | 所属模型范围 |
|--------|--------|--------------|
| **随机森林 & 决策树** | | |
| criterion | ['mse', 'friedman_mse', 'mae', 'poisson', 'gini', 'entropy'] | 随机森林、决策树 |
| max_features | ['auto', 'sqrt', 'log2', None] | 随机森林、决策树 |
| **决策树** | | |
| splitter | ['best', 'random'] | 决策树 |
| **Logistic回归** | | |
| penalty | ['l1', 'l2', 'elasticnet', 'none'] | Logistic回归 |
| solver | ['lbfgs', 'liblinear', 'newton-cg', 'sag', 'saga'] | Logistic回归 |
| multi_class | ['auto', 'ovr', 'multinomial'] | Logistic回归 |
| class_weight | ['balanced', None] | Logistic回归 |
| **支持向量机** | | |
| kernel | ['linear', 'poly', 'rbf', 'sigmoid', 'precomputed'] | 支持向量机 |
| gamma | ['scale', 'auto'] | 支持向量机 |
| **KNN** | | |
| weights | ['uniform', 'distance'] | KNN |
| algorithm | ['auto', 'ball_tree', 'kd_tree', 'brute'] | KNN |
| metric | ['minkowski', 'euclidean', 'manhattan', 'chebyshev', 'precomputed'] | KNN |
| **梯度提升树** | | |
| init | [None] | 梯度提升树（可扩展为estimator） |