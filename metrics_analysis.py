#!/usr/bin/env python3
"""
Comprehensive Software Metrics Analysis Report
Analyzes: COCOMO, Halstead, FPA, CFD, Throughput, Burndown, Burnup, LOC, Cyclomatic Complexity
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import subprocess

class MetricsAnalyzer:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.python_files = list(self.root_dir.glob('**/*.py'))
        self.metrics = {}

    def get_file_lines(self, filepath):
        """Get lines of code (LOC) stats for a file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            total = len(lines)
            code = 0
            comments = 0
            blanks = 0

            in_multiline = False
            for line in lines:
                stripped = line.strip()

                # Multiline strings/comments
                if '"""' in stripped or "'''" in stripped:
                    in_multiline = not in_multiline
                    comments += 1
                    continue

                if in_multiline:
                    comments += 1
                elif stripped.startswith('#'):
                    comments += 1
                elif not stripped:
                    blanks += 1
                else:
                    code += 1

            return {'total': total, 'code': code, 'comments': comments, 'blank': blanks}
        except:
            return {'total': 0, 'code': 0, 'comments': 0, 'blank': 0}

    def analyze_halstead_metrics(self):
        """Calculate Halstead Complexity Metrics"""
        operators = defaultdict(int)
        operands = defaultdict(int)

        # Python operators
        op_pattern = r'(\+|-|\*|/|==|!=|<=|>=|<|>|and|or|not|=|+=|-=|in|is)'

        for filepath in self.python_files:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Count operators
                for match in re.finditer(op_pattern, content):
                    operators[match.group()] += 1

                # Count operands (variables, literals, functions)
                words = re.findall(r'\b[a-zA-Z_]\w*\b', content)
                for word in words:
                    if word not in ['def', 'class', 'if', 'else', 'for', 'while', 'return', 'import', 'from']:
                        operands[word] += 1
            except:
                pass

        n1 = len(operators)  # Unique operators
        n2 = len(operands)   # Unique operands
        N1 = sum(operators.values())  # Total operators
        N2 = sum(operands.values())   # Total operands

        if n1 > 0 and n2 > 0 and N1 > 0 and N2 > 0:
            program_length = N1 + N2
            program_vocabulary = n1 + n2
            volume = program_length * (len(bin(program_vocabulary)) - 2)
            difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
            effort = difficulty * volume
            time_minutes = effort / 60 if effort > 0 else 0
            bugs = effort ** (2/3) / 3000 if effort > 0 else 0

            return {
                'n1_unique_operators': n1,
                'n2_unique_operands': n2,
                'N1_total_operators': N1,
                'N2_total_operands': N2,
                'program_length': program_length,
                'program_vocabulary': program_vocabulary,
                'volume': round(volume, 2),
                'difficulty': round(difficulty, 2),
                'effort': round(effort, 2),
                'time_minutes': round(time_minutes, 2),
                'estimated_bugs': round(bugs, 2)
            }
        return {}

    def analyze_cocomo_intermediate(self):
        """Intermediate COCOMO Model Analysis"""
        loc = sum(self.get_file_lines(f)['code'] for f in self.python_files)
        kloc = loc / 1000 if loc > 0 else 0.1

        # Project characteristics
        has_gui = any('ui' in f.name.lower() or 'gui' in f.name.lower() for f in self.python_files)
        has_ml = any('rl' in f.name.lower() or 'agent' in f.name.lower() for f in self.python_files)
        has_testing = any('test' in str(f) for f in self.python_files)

        # Complexity multiplier (1.0 - 1.4)
        complexity_multiplier = 1.0
        if has_ml:
            complexity_multiplier += 0.2
        if has_gui:
            complexity_multiplier += 0.1

        # COCOMO formula: Effort = a * (KLOC)^b
        a = 3.2
        b = 1.05

        effort_months = a * (kloc ** b)
        schedule_months = 2.4 * (effort_months ** 0.35)
        team_size = effort_months / schedule_months if schedule_months > 0 else 0

        return {
            'lines_of_code': loc,
            'kloc': round(kloc, 2),
            'a_coefficient': a,
            'b_exponent': b,
            'complexity_multiplier': complexity_multiplier,
            'effort_person_months': round(effort_months * complexity_multiplier, 2),
            'schedule_months': round(schedule_months, 2),
            'recommended_team_size': round(team_size, 1),
            'project_characteristics': {
                'has_gui': has_gui,
                'has_ml_components': has_ml,
                'has_testing': has_testing
            }
        }

    def analyze_function_points(self):
        """Function Point Analysis (Simplified)"""
        # Count function definitions as proxy for function points
        function_count = 0
        class_count = 0
        input_count = 0
        output_count = 0

        for filepath in self.python_files:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                function_count += len(re.findall(r'def\s+\w+\s*\(', content))
                class_count += len(re.findall(r'class\s+\w+', content))
                input_count += len(re.findall(r'input\(|\.get\(|request\.', content))
                output_count += len(re.findall(r'print\(|return\s|\.append\(|\.write\(', content))
            except:
                pass

        # Simplified FP calculation
        inputs_fp = input_count * 3
        outputs_fp = output_count * 4
        inquiries_fp = class_count * 3
        files_fp = len(self.python_files) * 7
        interfaces_fp = function_count * 5

        total_fpa = inputs_fp + outputs_fp + inquiries_fp + files_fp + interfaces_fp
        complexity_factor = 0.65  # Moderate complexity
        adjusted_fpa = total_fpa * complexity_factor

        return {
            'functions': function_count,
            'classes': class_count,
            'inputs': input_count,
            'outputs': output_count,
            'files': len(self.python_files),
            'inputs_fp': inputs_fp,
            'outputs_fp': outputs_fp,
            'inquiries_fp': inquiries_fp,
            'files_fp': files_fp,
            'interface_fp': interfaces_fp,
            'total_fpa': total_fpa,
            'complexity_factor': complexity_factor,
            'adjusted_fpa': round(adjusted_fpa, 2),
            'estimated_effort_hours': round(adjusted_fpa * 0.5, 2)
        }

    def analyze_cyclomatic_complexity(self):
        """Calculate Cyclomatic Complexity (CC)"""
        total_cc = 0
        file_cc = []

        for filepath in self.python_files:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                cc = 1
                for line in lines:
                    if re.search(r'\b(if|elif|else|for|while|except|and|or)\b', line):
                        if 'elif' not in line:
                            cc += 1

                file_cc.append({'file': filepath.name, 'cc': cc})
                total_cc += cc
            except:
                pass

        avg_cc = total_cc / len(self.python_files) if self.python_files else 0

        return {
            'total_cyclomatic_complexity': total_cc,
            'average_cc': round(avg_cc, 2),
            'high_complexity_files': [f for f in file_cc if f['cc'] > 10],
            'complexity_classification': 'Moderate' if avg_cc < 10 else 'High' if avg_cc < 20 else 'Very High'
        }

    def analyze_lines_of_code(self):
        """Detailed LOC Analysis"""
        total_loc = {'code': 0, 'comments': 0, 'blank': 0, 'total': 0}
        file_stats = []

        for filepath in self.python_files:
            stats = self.get_file_lines(filepath)
            file_stats.append({'file': filepath.name, **stats})
            for key in total_loc:
                total_loc[key] += stats[key]

        doc_ratio = total_loc['comments'] / total_loc['code'] if total_loc['code'] > 0 else 0

        return {
            'total_code_lines': total_loc['code'],
            'total_comment_lines': total_loc['comments'],
            'total_blank_lines': total_loc['blank'],
            'total_lines': total_loc['total'],
            'documentation_ratio': round(doc_ratio, 2),
            'top_files': sorted(file_stats, key=lambda x: x['code'], reverse=True)[:5]
        }

    def get_git_metrics(self):
        """Extract metrics from git history"""
        try:
            os.chdir(self.root_dir)

            # Get commits
            result = subprocess.run(['git', 'log', '--oneline'], capture_output=True, text=True)
            commits = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0

            # Get contributors
            result = subprocess.run(['git', 'log', '--format=%an'], capture_output=True, text=True)
            contributors = len(set(result.stdout.strip().split('\n'))) if result.stdout.strip() else 0

            # Get commit dates
            result = subprocess.run(['git', 'log', '--format=%ci'], capture_output=True, text=True)
            dates = result.stdout.strip().split('\n') if result.stdout.strip() else []

            return {
                'total_commits': commits,
                'contributors': contributors,
                'recent_commits': min(commits, 10)
            }
        except:
            return {'total_commits': 0, 'contributors': 0, 'recent_commits': 0}

    def generate_sprint_burndown(self):
        """Simulated Sprint Burndown (based on commits)"""
        git_metrics = self.get_git_metrics()
        sprint_days = 14
        total_commits = git_metrics['total_commits']

        # Simulate burndown
        planned_work = total_commits * 8  # Assume 8 story points per commit
        remaining_work = list(range(planned_work, 0, -int(planned_work / sprint_days))) + [0]

        return {
            'sprint_duration_days': sprint_days,
            'planned_story_points': planned_work,
            'days': list(range(0, min(len(remaining_work), sprint_days + 1))),
            'remaining_work': remaining_work[:sprint_days + 1],
            'ideal_burndown': list(range(planned_work, -int(planned_work / sprint_days), -int(planned_work / sprint_days)))[:sprint_days + 1]
        }

    def generate_sprint_burnup(self):
        """Simulated Sprint Burnup"""
        burndown = self.generate_sprint_burndown()
        planned = burndown['planned_story_points']
        remaining = burndown['remaining_work']

        completed = [planned - r for r in remaining]

        return {
            'days': burndown['days'],
            'completed_work': completed,
            'scope': [planned] * len(burndown['days']),
            'completion_rate': f"{(completed[-1] / planned * 100) if planned > 0 else 0:.1f}%"
        }

    def generate_cumulative_flow(self):
        """Simulated Cumulative Flow Diagram"""
        git_metrics = self.get_git_metrics()
        total_commits = git_metrics['total_commits']

        days = list(range(total_commits))
        backlog = [total_commits - i for i in range(total_commits)]
        progress = list(range(total_commits))
        completed = list(range(total_commits))

        return {
            'days': days,
            'backlog': backlog,
            'progress': progress,
            'completed': completed,
            'total_items': total_commits
        }

    def generate_throughput_report(self):
        """Throughput Report (commits per day)"""
        try:
            os.chdir(self.root_dir)
            result = subprocess.run(['git', 'log', '--format=%ci'], capture_output=True, text=True)

            commit_dates = defaultdict(int)
            for line in result.stdout.strip().split('\n'):
                if line:
                    date = line.split()[0]
                    commit_dates[date] += 1

            sorted_dates = sorted(commit_dates.items())

            return {
                'commits_by_date': dict(sorted_dates[-14:]) if len(sorted_dates) > 14 else dict(sorted_dates),
                'average_commits_per_day': round(sum(commit_dates.values()) / len(commit_dates), 2) if commit_dates else 0,
                'total_commits': sum(commit_dates.values()),
                'active_days': len(commit_dates)
            }
        except:
            return {'commits_by_date': {}, 'average_commits_per_day': 0, 'total_commits': 0, 'active_days': 0}

    def generate_report(self):
        """Generate complete metrics report"""
        print("=" * 80)
        print("COMPREHENSIVE SOFTWARE METRICS ANALYSIS REPORT")
        print("=" * 80)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project: {self.root_dir.name}")
        print(f"Python Files Analyzed: {len(self.python_files)}")
        print("=" * 80)

        # 1. Lines of Code Analysis
        print("\n1. LINES OF CODE (LOC) ANALYSIS")
        print("-" * 80)
        loc_metrics = self.analyze_lines_of_code()
        print(f"   Total Code Lines: {loc_metrics['total_code_lines']}")
        print(f"   Comment Lines: {loc_metrics['total_comment_lines']}")
        print(f"   Blank Lines: {loc_metrics['total_blank_lines']}")
        print(f"   Total Lines: {loc_metrics['total_lines']}")
        print(f"   Documentation Ratio: {loc_metrics['documentation_ratio']}")
        print(f"\n   Top 5 Files by LOC:")
        for f in loc_metrics['top_files'][:5]:
            print(f"      {f['file']}: {f['code']} LOC")

        # 2. COCOMO Analysis
        print("\n2. INTERMEDIATE COCOMO MODEL")
        print("-" * 80)
        cocomo = self.analyze_cocomo_intermediate()
        print(f"   Lines of Code: {cocomo['lines_of_code']}")
        print(f"   KLOC: {cocomo['kloc']}")
        print(f"   Estimated Effort: {cocomo['effort_person_months']} person-months")
        print(f"   Schedule: {cocomo['schedule_months']} months")
        print(f"   Recommended Team Size: {cocomo['recommended_team_size']} developers")
        print(f"   Complexity Multiplier: {cocomo['complexity_multiplier']}")
        print(f"   Project Type: ML/RL System with Testing")

        # 3. Halstead Metrics
        print("\n3. HALSTEAD COMPLEXITY METRICS")
        print("-" * 80)
        halstead = self.analyze_halstead_metrics()
        if halstead:
            print(f"   Unique Operators (n1): {halstead['n1_unique_operators']}")
            print(f"   Unique Operands (n2): {halstead['n2_unique_operands']}")
            print(f"   Total Operators (N1): {halstead['N1_total_operators']}")
            print(f"   Total Operands (N2): {halstead['N2_total_operands']}")
            print(f"   Program Length: {halstead['program_length']}")
            print(f"   Program Vocabulary: {halstead['program_vocabulary']}")
            print(f"   Volume: {halstead['volume']} bits")
            print(f"   Difficulty: {halstead['difficulty']}")
            print(f"   Effort: {halstead['effort']} elementary operations")
            print(f"   Time to Develop: {halstead['time_minutes']} minutes")
            print(f"   Estimated Bugs: {halstead['estimated_bugs']}")

        # 4. Function Point Analysis
        print("\n4. FUNCTION POINT ANALYSIS (FPA)")
        print("-" * 80)
        fpa = self.analyze_function_points()
        print(f"   Functions: {fpa['functions']}")
        print(f"   Classes: {fpa['classes']}")
        print(f"   Input Points: {fpa['inputs']}")
        print(f"   Output Points: {fpa['outputs']}")
        print(f"   Total Unadjusted FPA: {fpa['total_fpa']}")
        print(f"   Complexity Factor: {fpa['complexity_factor']}")
        print(f"   Adjusted Function Points: {fpa['adjusted_fpa']}")
        print(f"   Estimated Effort: {fpa['estimated_effort_hours']} hours")

        # 5. Cyclomatic Complexity
        print("\n5. CYCLOMATIC COMPLEXITY ANALYSIS")
        print("-" * 80)
        cc = self.analyze_cyclomatic_complexity()
        print(f"   Total Cyclomatic Complexity: {cc['total_cyclomatic_complexity']}")
        print(f"   Average CC per File: {cc['average_cc']}")
        print(f"   Complexity Classification: {cc['complexity_classification']}")
        if cc['high_complexity_files']:
            print(f"   High Complexity Files (CC > 10):")
            for f in cc['high_complexity_files']:
                print(f"      {f['file']}: {f['cc']}")

        # 6. Git Metrics
        print("\n6. GIT COMMIT METRICS & THROUGHPUT REPORT")
        print("-" * 80)
        git_metrics = self.get_git_metrics()
        throughput = self.generate_throughput_report()
        print(f"   Total Commits: {git_metrics['total_commits']}")
        print(f"   Contributors: {git_metrics['contributors']}")
        print(f"   Average Commits/Day: {throughput['average_commits_per_day']}")
        print(f"   Active Development Days: {throughput['active_days']}")
        if throughput['commits_by_date']:
            print(f"   Recent Commits (last 14 days):")
            for date, count in list(throughput['commits_by_date'].items())[-5:]:
                print(f"      {date}: {count} commit(s)")

        # 7. Sprint Burndown
        print("\n7. SPRINT BURNDOWN CHART (SIMULATED)")
        print("-" * 80)
        burndown = self.generate_sprint_burndown()
        print(f"   Sprint Duration: {burndown['sprint_duration_days']} days")
        print(f"   Planned Story Points: {burndown['planned_story_points']}")
        print(f"   Day | Remaining Work")
        for day, work in zip(burndown['days'][:8], burndown['remaining_work'][:8]):
            bar = "#" * max(0, int(work / 10))
            print(f"   {day:2d}  | {work:4d} {bar}")

        # 8. Sprint Burnup
        print("\n8. SPRINT BURNUP CHART (SIMULATED)")
        print("-" * 80)
        burnup = self.generate_sprint_burnup()
        print(f"   Completion Rate: {burnup['completion_rate']}")
        print(f"   Day | Completed Work")
        for day, completed in zip(burnup['days'][:8], burnup['completed_work'][:8]):
            bar = "#" * max(0, int(completed / 10))
            print(f"   {day:2d}  | {completed:4d} {bar}")

        # 9. Cumulative Flow Diagram
        print("\n9. CUMULATIVE FLOW DIAGRAM (CFD)")
        print("-" * 80)
        cfd = self.generate_cumulative_flow()
        print(f"   Total Items: {cfd['total_items']}")
        print(f"   Sample Data Points:")
        for i, day in enumerate(cfd['days'][::max(1, len(cfd['days'])//5)]):
            idx = i * max(1, len(cfd['days'])//5)
            if idx < len(cfd['days']):
                print(f"      Day {day}: Backlog={cfd['backlog'][idx]}, Progress={cfd['progress'][idx]}, Completed={cfd['completed'][idx]}")

        # 10. Additional Metrics Summary
        print("\n10. ADDITIONAL METRICS SUMMARY")
        print("-" * 80)
        print(f"   Code-to-Comment Ratio: {round(loc_metrics['total_code_lines'] / max(1, loc_metrics['total_comment_lines']), 2)}:1")
        print(f"   Average Functions per File: {round(fpa['functions'] / len(self.python_files), 2)}")
        print(f"   Average Classes per File: {round(fpa['classes'] / len(self.python_files), 2)}")
        print(f"   Development Velocity (commits): {git_metrics['total_commits']} commits")
        print(f"   Technical Debt Indicator: {'Low' if cc['average_cc'] < 10 else 'Moderate' if cc['average_cc'] < 15 else 'High'}")

        print("\n" + "=" * 80)
        print("END OF REPORT")
        print("=" * 80)

if __name__ == '__main__':
    analyzer = MetricsAnalyzer('c:/Users/PC/Desktop/CAPR_LB2/CAPR_LB')
    analyzer.generate_report()
