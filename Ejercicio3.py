class RegisterAllocator:
    def __init__(self):
        # Inicializamos los 3 registros como None
        self.registers = [None, None, None]  # Representa R1, R2, R3
        # Memoria para spill (variables derramadas)
        self.memory = {}

    def get_register(self, variable):
        """
        Asigna un registro a la variable.
        - Si ya está en un registro, devuelve el índice.
        - Si hay un registro libre, lo asigna.
        - Si no hay registros libres, hace spill y asigna el registro liberado.
        """
        # 1. Si la variable ya está en un registro, devolverlo
        if variable in self.registers:
            reg_index = self.registers.index(variable)
            print(f"{variable} ya está en R{reg_index+1}")
            return reg_index

        # 2. Si hay registro libre, asignarlo
        if None in self.registers:
            free_index = self.registers.index(None)
            self.registers[free_index] = variable
            print(f"Asigna {variable} -> R{free_index+1}")
            return free_index

        # 3. Si no hay registro libre, hacer spill
        return self.spill_and_assign(variable)

    def spill_and_assign(self, variable):
        """
        Derrama el valor de un registro a la memoria
        y asigna la nueva variable al registro liberado.
        Política: spill el primer registro (R1).
        """
        spilled_var = self.registers[0]  # Elegimos R1 para spill
        self.memory[spilled_var] = f"mem_{spilled_var}"
        print(f"Spill de {spilled_var} a memoria -> asigna {variable} en R1")
        self.registers[0] = variable
        return 0  # Devuelve el índice del registro asignado (R1)

    def __str__(self):
        # Devuelve el estado de los registros y la memoria
        reg_state = ", ".join([f"R{i+1}:{v}" for i, v in enumerate(self.registers)])
        mem_state = ", ".join([f"{k}->{v}" for k, v in self.memory.items()]) or "Vacía"
        return f"Registros: [{reg_state}] | Memoria: [{mem_state}]"


# ====================
# CASOS DE PRUEBA
# ====================
if __name__ == "__main__":
    allocator = RegisterAllocator()
    allocator.get_register('a')  # R1
    allocator.get_register('b')  # R2
    allocator.get_register('c')  # R3
    allocator.get_register('d')  # Spill de a, asigna d a R1
    print(allocator)
